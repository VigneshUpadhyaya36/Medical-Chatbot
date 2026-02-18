# app.py
import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# LangChain community modules
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama

# Pinecone
from langchain_pinecone import Pinecone as PineconeVectorStore # 1. Import the VectorStore class with an alias
from pinecone import Pinecone as PineconeClient
from src.prompt import system_prompt

# Load environment variables
load_dotenv()

# ========================================
# CONSTANTS
# ========================================
INDEX_NAME = "medical-chatbot"
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')

if not PINECONE_API_KEY:
    raise ValueError("❌ PINECONE_API_KEY not found in .env file!")

# ========================================
# INITIALIZE COMPONENTS
# ========================================

print("🔧 Initializing Medical Chatbot...")

# Embeddings (same as used in store_index.py)
print("📦 Loading embeddings model...")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2", # This is the smallest/fastest model
    model_kwargs={'device': 'cpu'}  # Force CPU because Render has no GPU
)

# Pinecone vector store
print("☁️  Connecting to Pinecone...")
try:
    docsearch = PineconeVectorStore.from_existing_index(
        index_name=INDEX_NAME,
        embedding=embeddings
    )
    retriever = docsearch.as_retriever(search_kwargs={"k": 5})
    print("✅ Connected to Pinecone successfully")
except Exception as e:
    print(f"❌ Failed to connect to Pinecone: {e}")
    print("💡 Make sure you ran 'python store_index.py' first!")
    raise

# Ollama LLM
print("🤖 Connecting to Ollama...")
try:
    ollama_llm = Ollama(model="deepseek-r1:8b")
    print("✅ Connected to Ollama successfully")
except Exception as e:
    print(f"❌ Failed to connect to Ollama: {e}")
    print("💡 Make sure Ollama is running: 'ollama serve'")
    print("💡 And model is downloaded: 'ollama pull deepseek-r1:8b'")
    raise

# ========================================
# FLASK APP
# ========================================

app = Flask(__name__)

@app.route("/")
def index():
    """Render the chat interface"""
    return render_template("chat.html")


@app.route("/get", methods=["POST"])
def chat():
    """Handle chat requests"""
    try:
        # Get user message
        user_query = request.form.get("msg")
        
        if not user_query or user_query.strip() == "":
            return "⚠️ Please enter a question"
        
        print(f"\n📨 User query: {user_query}")
        
        # Retrieve relevant documents from Pinecone
        print("🔍 Searching knowledge base...")
        docs = retriever.invoke(user_query)
        
        if not docs:
            return "❌ I couldn't find relevant information in the knowledge base. Please try rephrasing your question."
        
        # Build context from retrieved documents
        context_text = "\n\n".join([doc.page_content for doc in docs])
        print(f"📚 Retrieved {len(docs)} relevant documents")
        
        # Build full prompt
        full_prompt = f"""{system_prompt}

Context from Medical Knowledge Base:
{context_text}

User Question: {user_query}

Answer:"""
        
        # Get response from Ollama
        print("💭 Generating response...")
        response = ollama_llm.invoke(full_prompt)
        
        print(f"✅ Response generated: {len(response)} characters")
        
        return str(response)
    
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return f"Sorry, an error occurred: {str(e)}"


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "index_name": INDEX_NAME,
        "model": "deepseek-r1:8b"
    })


# ========================================
# MAIN
# ========================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🏥 MEDICAL CHATBOT SERVER STARTING")
    print("="*60)
    print(f"🌐 Open browser: http://localhost:8080")
    print(f"🔍 Using Pinecone index: {INDEX_NAME}")
    print(f"🤖 Using Ollama model: deepseek-r1:8b")
    print("="*60 + "\n")
    
    app.run(host="0.0.0.0", port=8080, debug=True)