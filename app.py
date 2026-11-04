import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore
from src.prompt import system_prompt

load_dotenv()

INDEX_NAME = "medical-chatbot"
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

print("\n🔧 Initializing Medical Chatbot (Render/Groq Version)")

# 1. Load Embeddings (CPU optimized)
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)

# 2. Connect to Pinecone
try:
    docsearch = PineconeVectorStore.from_existing_index(
        index_name=INDEX_NAME,
        embedding=embeddings
    )
    retriever = docsearch.as_retriever(search_kwargs={"k": 5})
    print("✅ Connected to Pinecone")
except Exception as e:
    print(f"❌ Pinecone error: {e}")

# 3. Connect to Groq 
try:
    llm = ChatGroq(
        model="openai/gpt-oss-20b",
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

        docs = retriever.invoke(user_query)
        context_text = "\n\n".join([doc.page_content for doc in docs])
        
        full_prompt = f"{system_prompt}\n\nContext:\n{context_text}\n\nQuestion: {user_query}\n\nAnswer:"
        response = llm.invoke(full_prompt)
        return response.content
    except Exception as e:
        print(f"❌ Error: {e}")
        return "Sorry, I encountered an error processing your request."

# MODULE 3: Service-Oriented Architecture (SOA) REST API Endpoint
@app.route("/api/chat", methods=["POST"])
def api_chat():
    try:
        data = request.get_json()
        if not data or "msg" not in data:
            return jsonify({"error": "No message provided"}), 400
            
        user_query = data.get("msg")
        docs = retriever.invoke(user_query)
        context_text = "\n\n".join([doc.page_content for doc in docs])
        
        full_prompt = f"{system_prompt}\n\nContext:\n{context_text}\n\nQuestion: {user_query}\n\nAnswer:"
        response = llm.invoke(full_prompt)
        
        return jsonify({
            "service": "Medical-RAG-API",
            "status": "success",
            "response": response.content
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
