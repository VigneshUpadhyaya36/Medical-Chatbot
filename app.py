import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Import Groq and Pinecone
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore

from src.prompt import system_prompt

load_dotenv()

# Configuration
INDEX_NAME = "medical-chatbot"
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# Error handling for missing keys
if not PINECONE_API_KEY:
    print("❌ Error: PINECONE_API_KEY is missing!")
if not GROQ_API_KEY:
    print("❌ Error: GROQ_API_KEY is missing!")

print("\n" + "="*70)
print("🔧 Initializing Medical Chatbot (Render/Groq Version)")
print("="*70)

# 1. Load Embeddings (CPU optimized)
print("\n📦 Loading embeddings...")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)
print("✅ Embeddings loaded")

# 2. Connect to Pinecone
print("\n☁️ Connecting to Pinecone...")
try:
    docsearch = PineconeVectorStore.from_existing_index(
        index_name=INDEX_NAME,
        embedding=embeddings
    )
    retriever = docsearch.as_retriever(search_kwargs={"k": 5})
    print(f"✅ Connected to Pinecone Index: {INDEX_NAME}")
except Exception as e:
    print(f"❌ Pinecone error: {e}")

# 3. Connect to Groq (The Brain)
print("\n🤖 Connecting to Groq...")
try:
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.2,
        groq_api_key=GROQ_API_KEY
    )
    print("✅ Connected to Groq")
except Exception as e:
    print(f"❌ Groq error: {e}")

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/get", methods=["POST"])
def chat():
    try:
        user_query = request.form.get("msg")
        if not user_query:
            return "⚠️ Please enter a question"

        print(f"\n📨 Query: {user_query}")
        
        # Retrieve docs
        docs = retriever.invoke(user_query)
        context_text = "\n\n".join([doc.page_content for doc in docs])
        
        # Generate Answer
        full_prompt = f"""{system_prompt}

Context:
{context_text}

Question: {user_query}

Answer:"""
        
        response = llm.invoke(full_prompt)
        return response.content
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return "Sorry, I encountered an error processing your request."

if __name__ == "__main__":
    # Render sets the PORT env variable automatically
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
