# 1. Install dependencies
!pip install pyspark pinecone-client sentence-transformers langchain-pinecone langchain-huggingface pypdf langchain-text-splitters -q

import os
import re
from pyspark.sql import SparkSession
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from google.colab import files

print("📤 Please upload your Medical PDF (or cancel to use demo data)...")
uploaded = files.upload()

# Extract text from the uploaded PDF
medical_corpus = []
if uploaded:
    filename = list(uploaded.keys())[0]
    reader = PdfReader(filename)
    for page in reader.pages:
        text = page.extract_text()
        if text:
            medical_corpus.extend(text.split('. '))
    print(f"✅ Successfully loaded {len(medical_corpus)} sentences from {filename}")
else:
    print("⚠️ No PDF uploaded. Using simulated demo corpus.")
    medical_corpus = ["Patient exhibits severe cough and acute shoulder stiffness."]

# 2. Initialize Apache Spark MapReduce
spark = SparkSession.builder.appName("MedicalMapReduce").master("local[*]").getOrCreate()
sc = spark.sparkContext
rdd = sc.parallelize(medical_corpus)

# 3. MAP PHASE
def map_symptoms(sentence):
    target_symptoms = ["cough", "stiffness", "fever", "pain", "inflammation", "headache", "nausea"]
    words = re.findall(r'\b\w+\b', sentence.lower())
    return [(word, sentence) for word in words if word in target_symptoms]

mapped_data = rdd.flatMap(map_symptoms)
print(f"\n🗺️ MAP PHASE COMPLETE: Generated {mapped_data.count()} key-value pairs.")

# 4. REDUCE PHASE
def reduce_contexts(context1, context2):
    return context1 + " | " + context2

reduced_data = mapped_data.reduceByKey(reduce_contexts)
consolidated_results = reduced_data.collect()
print(f"\n📉 REDUCE PHASE COMPLETE: Consolidated into {len(consolidated_results)} symptom profiles.")

# 5. SAFE CHUNKING & PINECONE INGESTION
os.environ['PINECONE_API_KEY'] = "pcsk_3uQADo_23gXuf1mpwdcVzYgbpt2BmyXiaA6QJh5dyZjzo2vRfXTr4XrQSbdhyzQfKoU635" # Insert your API key here
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={'device': 'cpu'})

# Initialize the text splitter to respect Pinecone's 40KB limit
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=4000, 
    chunk_overlap=200
)

docs_to_embed = []
for symptom, aggregated_context in consolidated_results:
    # Create the massive document
    doc = Document(page_content=f"SYMPTOM: {symptom.upper()}\nDATA: {aggregated_context}")
    # Split the massive document into Pinecone-safe chunks
    safe_chunks = text_splitter.split_documents([doc])
    docs_to_embed.extend(safe_chunks)

print(f"\n✂️ CHUNKING COMPLETE: Split massive profiles into {len(docs_to_embed)} database-safe vectors.")
print("☁️ Uploading to Pinecone...")

try:
    PineconeVectorStore.from_documents(docs_to_embed, embeddings, index_name="medical-chatbot")
    print("✅ SUCCESS: MapReduce data live in Pinecone without exceeding memory limits!")
except Exception as e:
    print(f"⚠️ Vector upload failed. Details: {e}")
