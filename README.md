# Medical-Chatbot
link- http://clinical-medbot-ai.duckdns.org/

<img width="1600" height="819" alt="arch diagram" src="https://github.com/user-attachments/assets/67887ca7-d68f-41b0-b701-c2cfefa72699" />

<img width="1381" height="926" alt="image" src="https://github.com/user-attachments/assets/7048db65-ef20-4390-9c0f-12795abb8a0f" />
<img width="1421" height="940" alt="Screenshot 2026-02-14 224141" src="https://github.com/user-attachments/assets/85866679-f047-4878-987f-82b58eb5a098" />



# 🩺 Medical AI Clinical Assistant (RAG-Powered)

An enterprise-grade, HIPAA-compliant Medical RAG (Retrieval-Augmented Generation) Chatbot designed to process a massive 640-page clinical encyclopedia. The system bridges **Big Data batch processing (Module 4 MapReduce)** with a **real-time cloud-native Platform-as-a-Service (PaaS) deployment**, ensuring ultra-low latency inference and strict resource isolation.

---

## 🏗️ System Architecture & Dual-Phase Workflow

The architecture is split into two completely decoupled execution environments to optimize cloud compute resources:

```
[ Phase 1: Offline Big Data Ingestion ]           [ Phase 2: Real-time Live Inference ]
 640-Page PDF ──> PySpark (MapReduce) ──> Pinecone   User Prompt ──> Render (Flask PaaS) ──> Groq LPU
                 (Google Colab)       (Vector DB)                      │                  ▲
                                                                       └──────(Retrieval)─┘
```

### Phase 1: Offline Big Data Ingestion (Module 4 - MapReduce)
Instead of running heavy batch workloads on a live web server, raw clinical text is processed offline using **Apache Spark (PySpark)**, implementing the classic MapReduce paradigm:
1. **Map Phase:** Scans thousands of raw sentences from the clinical corpus and extracts target symptom key-value pairs (`(symptom_keyword, text_sentence)`).
2. **Sort & Group Phase:** Automatically shuffles and groups identical medical keys together.
3. **Reduce Phase:** Aggregates scattered data points into consolidated, hyper-dense symptom knowledge profiles.
4. **Vector Embedding & Storage:** The reduced data is tokenized using HuggingFace (`all-MiniLM-L6-v2`) and persistently uploaded to a **Pinecone Vector Database**.

### Phase 2: Real-Time PaaS Inference (v2 Render Deployment)
1. **Ingress & Routing:** User requests enter via the web UI or the decoupled **SOA REST API endpoint** (`/api/chat`), passing through Render's managed TLS 1.3 reverse proxy.
2. **Vectorization & Retrieval:** The Flask backend converts the live query into a mathematical embedding vector and queries Pinecone, instantaneously matching it against the Colab-processed MapReduce chunks using Cosine Similarity.
3. **LLM Inference Engine:** The retrieved context and user query are compiled into a strict system prompt and routed to **Groq's Language Processing Units (LPUs)** running `openai/gpt-oss-20b` for sub-second clinical responses.

---

## 🚀 Key Cloud Computing Features Implemented

* **Service Models (v1 vs. v2):** 
  * *v1 (AWS - Legacy):* Infrastructure-as-a-Service (IaaS) utilizing manual EC2 virtual machine provisioning, VPC subnets, and Nginx configurations.
  * *v2 (Render - Production):* Platform-as-a-Service (PaaS) utilizing ephemeral, containerized Linux runtimes paired with automated GitHub Actions CI/CD workflows.
* **Service-Oriented Architecture (SOA):** Decouples the frontend UI from backend logic via a standard RESTful JSON interface (`/api/chat`), allowing third-party services to consume the medical RAG pipeline seamlessly.
* **Cloud Security & Compliance:** Zero hardcoded API keys; secrets injected via secure environment variables. Data-in-transit secured via TLS; data-at-rest secured via Pinecone's enterprise encryption tier.

---

## 📂 Project Structure

```text
Medical-Chatbot/
├── app.py                     # Main Flask backend application & SOA endpoints
├── requirements.txt           # CPU-optimized Python dependencies & PyTorch configuration
├── mapreduce_offline_pipeline.py # PySpark MapReduce script for offline data ingestion
├── src/
│   └── prompt.py              # Clinical system instructions and LLM behavioral rules
├── templates/
│   └── chat.html              # Interactive frontend chat interface
└── README.md                  # Project documentation
```

---

## ⚙️ Local Setup & Deployment Instructions

### 1. Prerequisites
* Python 3.10+
* Active API keys for **Pinecone** and **Groq**.

### 2. Local Installation
```bash
# Clone the repository
git clone https://github.com/VigneshUpadhyaya36/Medical-Chatbot.git
cd Medical-Chatbot

# Install dependencies (forced CPU-optimized PyTorch build)
pip install -r requirements.txt

# Create a local .env file
echo "PINECONE_API_KEY=your_pinecone_key" > .env
echo "GROQ_API_KEY=your_groq_key" >> .env

# Run the application locally
python app.py
```

---

## 🔌 API Documentation (SOA Endpoint)

To test the Service-Oriented Architecture (SOA) JSON interface:

* **Endpoint:** `/api/chat`
* **Method:** `POST`
* **Content-Type:** `application/json`

**Request Body:**
```json
{
  "msg": "What are the treatment options for severe shoulder stiffness?"
}
```

**Response:**
```json
{
  "service": "Medical-RAG-API",
  "status": "success",
  "response": "Based on clinical guidelines, rest and physiotherapy are recommended..."
}
```

---

## 📜 License
Developed for academic demonstration and cloud computing architectural evaluation.


