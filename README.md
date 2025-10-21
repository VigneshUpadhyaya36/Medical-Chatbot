# Medical-Chatbot
Complete Setup Guide - Medical Chatbot with Flask
Prerequisites

Python 3.8+ installed (check with python --version)
Windows PowerShell
Pinecone account (free tier works)
Your medical data as .txt files


STEP 1: Create Project Structure
powershell# Create project folder
mkdir medical-chatbot
cd medical-chatbot

# Create subfolders
mkdir data
mkdir src
mkdir templates

STEP 2: Create Virtual Environment (NO ANACONDA)
powershell# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Then try activating again
You should see (venv) at the start of your terminal line.

STEP 3: Install All Dependencies
powershell# Upgrade pip first
python -m pip install --upgrade pip

# Install core dependencies
pip install flask
pip install python-dotenv

# Install LangChain components
pip install langchain
pip install langchain-community
pip install langchain-pinecone
pip install langchain-text-splitters

# Install embeddings and vector store
pip install sentence-transformers
pip install pinecone-client

# Install Ollama (for local LLM)
# Download Ollama from: https://ollama.com/download
# After installing Ollama, open a NEW PowerShell and run:
# ollama pull deepseek-r1:8b

STEP 4: Get Pinecone API Key

Go to https://www.pinecone.io/
Sign up for free account
Create a new project
Go to "API Keys" section
Copy your API key


STEP 5: Create Environment File
Create .env file in project root:
powershell# Create .env file
echo PINECONE_API_KEY=your_actual_api_key_here > .env
```

Or manually create `.env` file with:
```
PINECONE_API_KEY=pc-xxxxxxxxxxxxxxxxxxxxxx

STEP 6: Create Required Files
File 1: src/prompt.py
powershell# Create the file
New-Item -Path "src\prompt.py" -ItemType File
Add this content to src/prompt.py:
pythonsystem_prompt = """
You are a helpful medical assistant. Use the provided context to answer the user's question accurately.
If you don't know the answer based on the context, say so clearly.
Always provide information in a clear, professional manner.
"""

File 2: templates/chat.html
powershell# Create the file
New-Item -Path "templates\chat.html" -ItemType File

File 3: store_index.py
Save the store_index.py code you provided to the root folder.

File 4: app.py
Save the app.py code you provided to the root folder.

STEP 7: Prepare Your Data

Convert your medical PDF to .txt format
Place the .txt file(s) in the data/ folder
Name it something like Medical_book.txt


STEP 8: Build the Knowledge Base (ONE-TIME SETUP)
powershell# Make sure you're in the project root with venv activated
python store_index.py
```

This will:
- Load your medical text data
- Split it into chunks
- Create embeddings
- Upload to Pinecone
- **Takes 5-15 minutes depending on data size**

You'll see output like:
```
Loading pre-processed TXT data...
Total chunks created: 1234
Embedding model loaded.
✅ Pinecone Index population complete. Data is ready for retrieval.

STEP 9: Start Ollama (IMPORTANT)
Open a NEW PowerShell window and run:
powershell# Make sure Ollama is running
ollama serve
Keep this window open while using the chatbot.

STEP 10: Run the Flask App
Back in your original PowerShell (with venv activated):
powershellpython app.py
```

You should see:
```
 * Running on http://0.0.0.0:8080
 * Running on http://127.0.0.1:8080

STEP 11: Use the Chatbot!

Open your browser
Go to: http://localhost:8080
You should see the medical chatbot interface
Type a medical question and press Send!
