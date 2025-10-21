# store_index.py
import os
from typing import List
from dotenv import load_dotenv

# FIXED: Use langchain_core instead of langchain.schema
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Pinecone imports
from pinecone import Pinecone as PineconeClient
from langchain_pinecone import Pinecone as PineconeVectorStore # 1. Import the VectorStore class with an alias

# ========================================
# CONSTANTS
# ========================================
DATA_PATH = "./data"
INDEX_NAME = "medical-chatbot"

# Load environment variables
load_dotenv()
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')

if not PINECONE_API_KEY:
    raise ValueError("❌ PINECONE_API_KEY not found in .env file!")

# ========================================
# HELPER FUNCTIONS
# ========================================

def load_pdf_files(data_path: str) -> List[Document]:
    """
    Load all PDF files from the data directory.
    Each page becomes a separate Document.
    """
    print(f"📄 Loading PDF files from: {data_path}")
    
    loader = DirectoryLoader(
        data_path,
        glob="*.pdf",
        loader_cls=PyPDFLoader
    )
    
    documents = loader.load()
    print(f"✅ Loaded {len(documents)} pages from PDF(s)")
    return documents


def filter_to_minimal_docs(docs: List[Document]) -> List[Document]:
    """
    Clean up metadata - keep only 'source' field.
    This reduces noise and keeps things simple.
    """
    print("🧹 Cleaning document metadata...")
    
    minimal_docs: List[Document] = []
    for doc in docs:
        src = doc.metadata.get("source", "unknown")
        minimal_docs.append(
            Document(
                page_content=doc.page_content,
                metadata={"source": src}
            )
        )
    
    print(f"✅ Cleaned {len(minimal_docs)} documents")
    return minimal_docs


def text_split(minimal_docs: List[Document]) -> List[Document]:
    """
    Split documents into smaller chunks for better retrieval.
    
    chunk_size=500: Each chunk is ~500 characters
    chunk_overlap=20: 20 characters overlap between chunks to maintain context
    """
    print("✂️  Splitting documents into chunks...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=20,
    )
    
    text_chunks = text_splitter.split_documents(minimal_docs)
    print(f"✅ Created {len(text_chunks)} text chunks")
    return text_chunks


def create_embeddings():
    """
    Load the embedding model (runs locally, free, no API needed).
    This converts text into numerical vectors.
    """
    print("🤖 Loading embedding model...")
    
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    print("✅ Embedding model loaded (local, free)")
    return embeddings


def upload_to_pinecone(text_chunks: List[Document], embeddings, index_name: str):
    """
    Upload all chunks to Pinecone vector database.
    This is where the "magic" happens - your data becomes searchable.
    """
    print(f"☁️  Uploading to Pinecone index: {index_name}")
    print("⏳ This may take 5-15 minutes depending on data size...")
    
    # Connect to Pinecone
    pc = PineconeClient(api_key=PINECONE_API_KEY)
    
    # Create vector store (automatically creates index if it doesn't exist)
    docsearch = PineconeVectorStore.from_documents(
        documents=text_chunks,
        embedding=embeddings,
        index_name=index_name
    )
    
    print("✅ Upload complete! Your knowledge base is ready.")
    return docsearch


# ========================================
# MAIN EXECUTION
# ========================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🏥 MEDICAL CHATBOT - KNOWLEDGE BASE BUILDER")
    print("="*60 + "\n")
    
    try:
        # Step 1: Load PDF files
        extracted_docs = load_pdf_files(DATA_PATH)
        
        if len(extracted_docs) == 0:
            print("❌ No PDF files found in ./data folder!")
            print("💡 Make sure Medical_book.pdf is in the data/ folder")
            exit(1)
        
        # Step 2: Clean metadata
        minimal_docs = filter_to_minimal_docs(extracted_docs)
        
        # Step 3: Split into chunks
        text_chunks = text_split(minimal_docs)
        
        # Step 4: Load embedding model
        embeddings = create_embeddings()
        
        # Step 5: Upload to Pinecone
        docsearch = upload_to_pinecone(text_chunks, embeddings, INDEX_NAME)
        
        print("\n" + "="*60)
        print("🎉 SUCCESS! Knowledge base is ready!")
        print("="*60)
        print(f"📊 Total chunks indexed: {len(text_chunks)}")
        print(f"🔍 Index name: {INDEX_NAME}")
        print("\n💡 Next step: Run 'python app.py' to start the chatbot\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if Medical_book.pdf exists in ./data folder")
        print("2. Verify PINECONE_API_KEY in .env file")
        print("3. Make sure venv is activated")
        print("4. Try: pip install pypdf PyPDF2 langchain-core")