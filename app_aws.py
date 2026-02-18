# app_aws.py - AWS Deployment Version with Groq
import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore

from src.prompt import system_prompt

load_dotenv()

INDEX_NAME = "medical-chatbot"
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

if not PINECONE_API_KEY:
    raise ValueError("❌ PINECONE_API_KEY not found!")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found!")

print("\n" + "="*70)
print("🔧 Initializing Medical Chatbot (AWS Version)")
print("="*70)

print("\n📦 Loading embeddings...")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2", # This is the smallest/fastest model
    model_kwargs={'device': 'cpu'}  # Force CPU because Render has no GPU
)
print("✅ Embeddings loaded")

print("\n☁️  Connecting to Pinecone...")
try:
    docsearch = PineconeVectorStore.from_existing_index(
        index_name=INDEX_NAME,
        embedding=embeddings
    )
    retriever = docsearch.as_retriever(search_kwargs={"k": 5})
    print(f"✅ Connected to Pinecone")
except Exception as e:
    print(f"❌ Pinecone error: {e}")
    raise

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
    raise

print("\n✅ All components ready!\n")

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/get", methods=["POST"])
def chat():
    try:
        user_query = request.form.get("msg")
        
        if not user_query or user_query.strip() == "":
            return "⚠️ Please enter a question"
        
        print(f"\n📨 Query: {user_query}")
        
        docs = retriever.invoke(user_query)
        
        if not docs:
            return "❌ No relevant information found."
        
        print(f"✅ Retrieved {len(docs)} chunks")
        
        context_text = "\n\n".join([doc.page_content for doc in docs])
        
        full_prompt = f"""{system_prompt}

Context:
{context_text}

Question: {user_query}

Answer:"""
        
        print("💭 Generating response...")
        response = llm.invoke(full_prompt)
        
        answer = response.content if hasattr(response, 'content') else str(response)
        
        print(f"✅ Response: {len(answer)} chars\n")
        
        return answer
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return f"Sorry, error occurred."

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "llm": "groq"})

if __name__ == "__main__":
    print("🏥 MEDICAL CHATBOT SERVER (AWS)")
    print("🌐 Starting on port 8080...\n")
    app.run(host="0.0.0.0", port=8080, debug=False)