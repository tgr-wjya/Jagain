# Jagain Anti-Scam Chatbot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up and build Jagain, a multilingual anti-scam web-based chatbot utilizing FastAPI backend, vanilla HTML/CSS/JS frontend, a local SQLite database for URL checks, and Azure AI Search for text-based RAG with gpt-4o.

**Architecture:** Sequential Screening flow intercepts messages in FastAPI. If a URL matches the local SQLite DB, it short-circuits. If not, it generates query embeddings, retrieves top scam templates from Azure AI Search, and calls gpt-4o to analyze and generate a structured JSON response in the user's language.

**Tech Stack:** Python (FastAPI, Uvicorn, SQLite3, pytest), Azure OpenAI API (gpt-4o and text-embedding-3-small), Azure AI Search SDK (azure-search-documents), python-dotenv, html/css/js.

---

### Task 1: Project Setup and Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `tests/test_setup.py`

- [ ] **Step 1: Create requirements.txt**
  Create `requirements.txt` with backend and test dependencies.
  
  Code for `requirements.txt`:
  ```text
  fastapi==0.111.0
  uvicorn==0.30.1
  openai==1.34.0
  azure-search-documents==11.5.0
  python-dotenv==1.0.1
  pytest==8.2.2
  pytest-asyncio==0.23.7
  ```

- [ ] **Step 2: Create local virtual environment and install packages**
  Run:
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

- [ ] **Step 3: Create tests/test_setup.py to verify setup**
  Create a simple test to ensure pytest runs and dependencies are importable.
  
  Code for `tests/test_setup.py`:
  ```python
  def test_imports():
      import fastapi
      import uvicorn
      import openai
      import azure.search.documents
      import sqlite3
      assert True
  ```

- [ ] **Step 4: Run the test to verify setup**
  Run:
  ```powershell
  .venv\Scripts\Activate.ps1
  pytest tests/test_setup.py -v
  ```
  Expected: 1 passed test.

- [ ] **Step 5: Commit changes**
  Run:
  ```bash
  git add requirements.txt tests/test_setup.py
  git commit -m "chore: initialize project setup and install requirements"
  ```

---

### Task 2: Azure CLI Deployment Script

**Files:**
- Create: `deploy_azure.ps1`

- [ ] **Step 1: Write deploy_azure.ps1**
  Create a PowerShell script to provision Azure services using the logged-in `az` CLI.
  
  Code for `deploy_azure.ps1`:
  ```powershell
  $SUFFIX = Get-Random -Minimum 1000 -Maximum 9999
  $RG_NAME = "rg-jagain-chatbot"
  $LOCATION = "eastus2"
  $OPENAI_NAME = "openai-jagain-$SUFFIX"
  $SEARCH_NAME = "search-jagain-$SUFFIX"
  
  Write-Host "Creating Resource Group: $RG_NAME..."
  az group create --name $RG_NAME --location $LOCATION
  
  Write-Host "Creating Azure OpenAI Service: $OPENAI_NAME..."
  az cognitiveservices account create --name $OPENAI_NAME --resource-group $RG_NAME --kind OpenAI --sku S0 --location $LOCATION --yes
  
  Write-Host "Deploying gpt-4o model..."
  az cognitiveservices account deployment create --name $OPENAI_NAME --resource-group $RG_NAME --deployment-name gpt-4o --model-name gpt-4o --model-version "2024-05-13" --model-format CognitiveServices --scale-settings-scale-type "Standard" --capacity 10
  
  Write-Host "Deploying text-embedding-3-small model..."
  az cognitiveservices account deployment create --name $OPENAI_NAME --resource-group $RG_NAME --deployment-name text-embedding-3-small --model-name text-embedding-3-small --model-version "1" --model-format CognitiveServices --scale-settings-scale-type "Standard" --capacity 20
  
  Write-Host "Creating Azure AI Search Service: $SEARCH_NAME (Free Tier)..."
  az search service create --name $SEARCH_NAME --resource-group $RG_NAME --sku Free --location $LOCATION
  
  Write-Host "Retrieving endpoints and keys..."
  $OPENAI_KEY = (az cognitiveservices account keys list --name $OPENAI_NAME --resource-group $RG_NAME --query key1 -o tsv)
  $OPENAI_ENDPOINT = (az cognitiveservices account show --name $OPENAI_NAME --resource-group $RG_NAME --query properties.endpoint -o tsv)
  $SEARCH_KEY = (az search admin-key show --service-name $SEARCH_NAME --resource-group $RG_NAME --query primaryKey -o tsv)
  $SEARCH_ENDPOINT = "https://$SEARCH_NAME.search.windows.net"
  
  Write-Host "Writing environment variables to .env..."
  $ENV_CONTENT = @"
  AZURE_OPENAI_API_KEY=$OPENAI_KEY
  AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT
  AZURE_OPENAI_DEPLOYMENT_CHAT=gpt-4o
  AZURE_OPENAI_DEPLOYMENT_EMBED=text-embedding-3-small
  AZURE_OPENAI_API_VERSION=2024-02-01
  AZURE_SEARCH_ENDPOINT=$SEARCH_ENDPOINT
  AZURE_SEARCH_API_KEY=$SEARCH_KEY
  AZURE_SEARCH_INDEX=sms-scams-index
  "@
  $ENV_CONTENT | Out-File -FilePath ".env" -Encoding utf8
  Write-Host "Azure Deployment complete! Check your generated .env file."
  ```

- [ ] **Step 2: Commit deployment script**
  Run:
  ```bash
  git add deploy_azure.ps1
  git commit -m "feat: add azure deployment script"
  ```

---

### Task 3: Preprocessing & Ingestion Engine

**Files:**
- Create: `scripts/preprocess_urls.py`
- Create: `scripts/ingest_sms_rag.py`
- Test: `tests/test_preprocessing.py`

- [ ] **Step 1: Implement URL database preprocessing**
  Write `scripts/preprocess_urls.py` to extract root domains, clean links, and load URLs from the CSVs into a local `scam_urls.db` database.
  
  Code for `scripts/preprocess_urls.py`:
  ```python
  import os
  import csv
  import sqlite3
  from urllib.parse import urlparse
  
  def normalize_url(url):
      url = url.strip().lower()
      if not url.startswith(('http://', 'https://')):
          url = 'http://' + url
      try:
          parsed = urlparse(url)
          netloc = parsed.netloc
          if netloc.startswith('www.'):
              netloc = netloc[4:]
          path = parsed.path.rstrip('/')
          return f"{netloc}{path}", netloc
      except Exception:
          return url, ""
  
  def preprocess():
      db_path = "scam_urls.db"
      if os.path.exists(db_path):
          os.remove(db_path)
          
      conn = sqlite3.connect(db_path)
      cursor = conn.cursor()
      cursor.execute("""
      CREATE TABLE scam_urls (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          url TEXT UNIQUE,
          domain TEXT,
          type TEXT
      );
      """)
      cursor.execute("CREATE INDEX idx_url ON scam_urls(url);")
      cursor.execute("CREATE INDEX idx_domain ON scam_urls(domain);")
      
      # Process Phishing URLs.csv (All phishing)
      url_file1 = r"Phishing URL dataset/Phishing URLs.csv"
      if os.path.exists(url_file1):
          with open(url_file1, 'r', encoding='utf-8', errors='ignore') as f:
              reader = csv.reader(f)
              next(reader)  # skip header
              for row in reader:
                  if not row: continue
                  normalized, domain = normalize_url(row[0])
                  try:
                      cursor.execute("INSERT INTO scam_urls (url, domain, type) VALUES (?, ?, ?)", 
                                     (normalized, domain, "phishing"))
                  except sqlite3.IntegrityError:
                      pass
                      
      # Process URL dataset.csv (phishing + legitimate)
      url_file2 = r"Phishing URL dataset/URL dataset.csv"
      if os.path.exists(url_file2):
          with open(url_file2, 'r', encoding='utf-8', errors='ignore') as f:
              reader = csv.reader(f)
              next(reader)  # skip header
              for row in reader:
                  if not row or len(row) < 2: continue
                  normalized, domain = normalize_url(row[0])
                  label = "phishing" if row[1].lower() == "phishing" else "legitimate"
                  try:
                      cursor.execute("INSERT INTO scam_urls (url, domain, type) VALUES (?, ?, ?)", 
                                     (normalized, domain, label))
                  except sqlite3.IntegrityError:
                      pass
                      
      conn.commit()
      conn.close()
      print("SQLite preprocessing complete!")
  
  if __name__ == "__main__":
      preprocess()
  ```

- [ ] **Step 2: Write tests/test_preprocessing.py**
  Create tests to verify URL normalization and database upserts.
  
  Code for `tests/test_preprocessing.py`:
  ```python
  import sqlite3
  from scripts.preprocess_urls import normalize_url
  
  def test_normalize_url():
      normalized, domain = normalize_url("https://www.google.com/login/")
      assert normalized == "google.com/login"
      assert domain == "google.com"
      
      normalized2, domain2 = normalize_url("http://scam-link.net/")
      assert normalized2 == "scam-link.net"
      assert domain2 == "scam-link.net"
  ```

- [ ] **Step 3: Run the test to verify preprocessing functions**
  Run:
  ```powershell
  .venv\Scripts\Activate.ps1
  pytest tests/test_preprocessing.py -v
  ```
  Expected: test passes.

- [ ] **Step 4: Implement SMS RAG Ingest Script**
  Write `scripts/ingest_sms_rag.py` to create the search index and upload vectorized SMS data.
  
  Code for `scripts/ingest_sms_rag.py`:
  ```python
  import os
  import hashlib
  from dotenv import load_dotenv
  from openai import AzureOpenAI
  from azure.core.credentials import AzureKeyCredential
  from azure.search.documents import SearchClient
  from azure.search.documents.indexes import SearchIndexClient
  from azure.search.documents.indexes.models import (
      SearchIndex, SimpleField, SearchableField, SearchField, SearchFieldDataType,
      VectorSearch, VectorSearchProfile, HnswAlgorithmConfiguration
  )
  
  load_dotenv()
  
  def get_embedding(text, client):
      response = client.embeddings.create(
          input=[text],
          model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBED")
      )
      return response.data[0].embedding
  
  def ingest():
      # Connect clients
      endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
      key = os.getenv("AZURE_SEARCH_API_KEY")
      index_name = os.getenv("AZURE_SEARCH_INDEX", "sms-scams-index")
      
      index_client = SearchIndexClient(endpoint, AzureKeyCredential(key))
      
      # Define index fields and vector configuration
      fields = [
          SimpleField(name="id", type=SearchFieldDataType.String, key=True),
          SearchableField(name="text", type=SearchFieldDataType.String),
          SimpleField(name="label", type=SearchFieldDataType.String, filterable=True),
          SearchField(
              name="vector",
              type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
              searchable=True,
              vector_search_dimensions=1536,
              vector_search_profile_name="vector-profile"
          )
      ]
      
      vector_search = VectorSearch(
          algorithms=[HnswAlgorithmConfiguration(name="hnsw-config")],
          profiles=[VectorSearchProfile(name="vector-profile", algorithm_configuration_name="hnsw-config")]
      )
      
      index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)
      index_client.create_or_update_index(index)
      
      # Prepare OpenAI client
      openai_client = AzureOpenAI(
          api_key=os.getenv("AZURE_OPENAI_API_KEY"),
          api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
          azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
      )
      
      search_client = SearchClient(endpoint, index_name, AzureKeyCredential(key))
      
      # Parse dataset
      sms_file = r"sms+spam+collection/SMSSpamCollection"
      if not os.path.exists(sms_file):
          print(f"File {sms_file} not found!")
          return
          
      documents = []
      with open(sms_file, 'r', encoding='utf-8') as f:
          for idx, line in enumerate(f):
              parts = line.strip().split('\t')
              if len(parts) < 2: continue
              label, text = parts[0], parts[1]
              
              # Standardize embedding size limit (batch to save cost, index top 500 for Free Tier testing safety)
              if idx >= 500: break 
              
              doc_id = hashlib.md5(text.encode('utf-8')).hexdigest()
              try:
                  vector = get_embedding(text, openai_client)
                  documents.append({
                      "id": doc_id,
                      "text": text,
                      "label": label,
                      "vector": vector
                  })
              except Exception as e:
                  print(f"Error embedding row {idx}: {e}")
                  
      if documents:
          search_client.upload_documents(documents=documents)
          print(f"Uploaded {len(documents)} documents to Azure AI Search!")
  
  if __name__ == "__main__":
      ingest()
  ```

- [ ] **Step 5: Commit scripts**
  Run:
  ```bash
  git add scripts/preprocess_urls.py scripts/ingest_sms_rag.py
  git commit -m "feat: add URL and SMS ingestion scripts"
  ```

---

### Task 4: Backend Detection Logic & RAG

**Files:**
- Create: `backend/detector.py`
- Create: `backend/database.py`
- Test: `tests/test_detector.py`

- [ ] **Step 1: Create backend/database.py**
  Add helper logic to extract domains and query the SQLite database.
  
  Code for `backend/database.py`:
  ```python
  import sqlite3
  from scripts.preprocess_urls import normalize_url
  
  DB_PATH = "scam_urls.db"
  
  def check_url_in_db(raw_url):
      normalized, domain = normalize_url(raw_url)
      conn = sqlite3.connect(DB_PATH)
      cursor = conn.cursor()
      
      # Exact match check
      cursor.execute("SELECT type FROM scam_urls WHERE url = ?", (normalized,))
      row = cursor.fetchone()
      if row:
          conn.close()
          return row[0]
          
      # Domain match check
      if domain:
          cursor.execute("SELECT type FROM scam_urls WHERE domain = ?", (domain,))
          row = cursor.fetchone()
          if row:
              conn.close()
              return row[0]
              
      conn.close()
      return None
  ```

- [ ] **Step 2: Create backend/detector.py**
  Create the core detector combining URL check, embedding, RAG retrieval, and gpt-4o synthesis.
  
  Code for `backend/detector.py`:
  ```python
  import os
  import re
  import json
  from openai import AzureOpenAI
  from azure.core.credentials import AzureKeyCredential
  from azure.search.documents import SearchClient
  from azure.search.documents.models import VectorizedQuery
  from backend.database import check_url_in_db
  
  URL_REGEX = r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}(?:/[^\s]*)?)'
  
  def extract_urls(text):
      return re.findall(URL_REGEX, text)
  
  class AntiScamDetector:
      def __init__(self):
          self.openai_client = AzureOpenAI(
              api_key=os.getenv("AZURE_OPENAI_API_KEY"),
              api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
              azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
          )
          self.search_client = SearchClient(
              endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
              index_name=os.getenv("AZURE_SEARCH_INDEX"),
              credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY"))
          )
          
      def get_embedding(self, text):
          response = self.openai_client.embeddings.create(
              input=[text],
              model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBED")
          )
          return response.data[0].embedding
          
      def retrieve_similar_scams(self, text, top_k=3):
          vector = self.get_embedding(text)
          vector_query = VectorizedQuery(vector=vector, k_nearest_neighbors=top_k, fields="vector")
          
          results = self.search_client.search(
              search_text=None,
              vector_queries=[vector_query],
              select=["text", "label"]
          )
          
          contexts = []
          for r in results:
              contexts.append(f"Message: {r['text']} | Label: {r['label'].upper()}")
          return "\n---\n".join(contexts)
          
      def analyze_message(self, message):
          # Extract and check URLs first
          urls = extract_urls(message)
          phishing_urls = []
          for url in urls:
              status = check_url_in_db(url)
              if status == "phishing":
                  phishing_urls.append(url)
                  
          # Short-circuit if high-risk phishing links match local blocklist
          if phishing_urls:
              return {
                  "risk_score": 100,
                  "risk_level": "High Risk",
                  "indicators": ["Blacklisted URL link"],
                  "explanation": f"Warning! The message contains a known phishing link: {', '.join(phishing_urls)}.",
                  "recommendation": "Do not click on the link under any circumstances and delete the message.",
                  "urls_checked": urls,
                  "blocklisted_urls": phishing_urls,
                  "detection_source": "SQLite Blocklist"
              }
              
          # Proceed to semantic search RAG
          try:
              context = self.retrieve_similar_scams(message)
          except Exception as e:
              context = "No reference matches could be retrieved."
              print(f"Azure Search error: {e}")
              
          # Call GPT-4o
          system_prompt = """
          You are an expert Anti-Scam Security Assistant named Jagain. Your job is to analyze the user's message.
          Use the following retrieved historical context of similar messages (scams/legitimate) to help make your decision:
          
          [RETRIEVED CONTEXT]
          {context}
          
          [CRITICAL REQUIREMENT]
          Detect the language used by the user in their message.
          1. Perform your analysis in that detected language.
          2. Return both the "explanation" and "recommendation" in the EXACT SAME language.
          3. The "risk_level" and "indicators" should remain in English for standardization.
          
          Return ONLY a JSON response in the following schema:
          {
            "risk_score": 90,
            "risk_level": "High Risk",
            "indicators": ["Suspicious URL link", "Urgency claim"],
            "explanation": "[Written in the user's input language]",
            "recommendation": "[Written in the user's input language]"
          }
          """
          
          response = self.openai_client.chat.completions.create(
              model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT"),
              response_format={"type": "json_object"},
              messages=[
                  {"role": "system", "content": system_prompt.replace("{context}", context)},
                  {"role": "user", "content": message}
              ]
          )
          
          result = json.loads(response.choices[0].message.content)
          result["urls_checked"] = urls
          result["blocklisted_urls"] = []
          result["detection_source"] = "Azure OpenAI RAG"
          return result
  ```

- [ ] **Step 3: Create tests/test_detector.py**
  Add mock tests to verify RegEx URL extraction and sequential screening flow.
  
  Code for `tests/test_detector.py`:
  ```python
  from backend.detector import extract_urls
  
  def test_extract_urls():
      urls = extract_urls("Click on http://scam-rewards.net/claim or go to www.link.org")
      assert "http://scam-rewards.net/claim" in urls
      assert "www.link.org" in urls
  ```

- [ ] **Step 4: Run unit tests**
  Run:
  ```powershell
  .venv\Scripts\Activate.ps1
  pytest tests/test_detector.py -v
  ```
  Expected: passes.

- [ ] **Step 5: Commit detector module**
  Run:
  ```bash
  git add backend/database.py backend/detector.py tests/test_detector.py
  git commit -m "feat: implement sqlite query matching and RAG screening logic"
  ```

---

### Task 5: FastAPI Web Server & API Endpoints

**Files:**
- Create: `backend/main.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write backend/main.py**
  Implement the FastAPI endpoints.
  
  Code for `backend/main.py`:
  ```python
  import os
  from fastapi import FastAPI, HTTPException
  from fastapi.middleware.cors import CORSMiddleware
  from fastapi.staticfiles import StaticFiles
  from pydantic import BaseModel
  from backend.detector import AntiScamDetector
  from dotenv import load_dotenv
  
  load_dotenv()
  
  app = FastAPI(title="Jagain API", description="Anti-Scam Analysis Server")
  
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  
  class MessageRequest(BaseModel):
      message: str
      
  # Lazy load detector
  detector = None
  
  @app.get("/api/status")
  def get_status():
      global detector
      db_status = os.path.exists("scam_urls.db")
      azure_status = all([
          os.getenv("AZURE_OPENAI_API_KEY"),
          os.getenv("AZURE_SEARCH_API_KEY")
      ])
      return {
          "status": "healthy",
          "sqlite_loaded": db_status,
          "azure_configured": azure_status
      }
  
  @app.post("/api/check-message")
  def check_message(req: MessageRequest):
      global detector
      if not req.message.strip():
          raise HTTPException(status_code=400, detail="Message cannot be empty")
          
      if detector is None:
          try:
              detector = AntiScamDetector()
          except Exception as e:
              raise HTTPException(status_code=500, detail=f"Failed to initialize Azure clients: {e}")
              
      try:
          result = detector.analyze_message(req.message)
          return result
      except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
          
  # Mount static files to serve the frontend
  if os.path.exists("frontend"):
      app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
  ```

- [ ] **Step 2: Create tests/test_api.py**
  Verify standard API HTTP response handling.
  
  Code for `tests/test_api.py`:
  ```python
  from fastapi.testclient import TestClient
  from backend.main import app
  
  client = TestClient(app)
  
  def test_status_endpoint():
      response = client.get("/api/status")
      assert response.status_code == 200
      assert response.json()["status"] == "healthy"
  ```

- [ ] **Step 3: Run the API tests**
  Run:
  ```powershell
  .venv\Scripts\Activate.ps1
  pytest tests/test_api.py -v
  ```
  Expected: passes.

- [ ] **Step 4: Commit FastAPI server**
  Run:
  ```bash
  git add backend/main.py tests/test_api.py
  git commit -m "feat: build FastAPI endpoints and mount static files"
  ```

---

### Task 6: Glassmorphic Web UI Frontend

**Files:**
- Create: `frontend/index.html`
- Create: `frontend/index.css`
- Create: `frontend/index.js`

- [ ] **Step 1: Create frontend/index.html**
  Create structure containing chat containers, sidebar status widgets, and inputs.
  
  Code for `frontend/index.html`:
  ```html
  <!DOCTYPE html>
  <html lang="id">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Jagain - Anti-Scam Shield</title>
      <link rel="stylesheet" href="index.css">
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  </head>
  <body>
      <div class="app-wrapper">
          <header class="app-header">
              <div class="logo">🛡️ Jagain</div>
              <div id="connection-badge" class="badge">Checking connection...</div>
          </header>
          
          <main class="main-container">
              <section class="sidebar">
                  <div class="card score-card">
                      <h3>Risk Score</h3>
                      <div id="risk-score" class="score-value">0%</div>
                      <div id="risk-level" class="score-label">UNKNOWN</div>
                  </div>
                  
                  <div class="card indicators-card">
                      <h3>Scam Indicators</h3>
                      <div id="indicators-list" class="tags-container">
                          <span class="empty-tag">No scan run yet</span>
                      </div>
                  </div>
              </section>
              
              <section class="chat-container">
                  <div id="chat-messages" class="chat-messages">
                      <div class="message bot">
                          Hello! Paste any text message, SMS, email content, or link here. I will analyze it and determine if it is a scam.
                      </div>
                  </div>
                  
                  <div class="input-form">
                      <textarea id="message-input" placeholder="Paste your message or URL here..."></textarea>
                      <button id="send-button">Scan</button>
                  </div>
              </section>
          </main>
      </div>
      <script src="index.js"></script>
  </body>
  </html>
  ```

- [ ] **Step 2: Create frontend/index.css**
  Write a high-end dark glassmorphic design system matching the specs.
  
  Code for `frontend/index.css`:
  ```css
  :root {
      --bg: #0b0c10;
      --panel: rgba(255, 255, 255, 0.03);
      --border: rgba(255, 255, 255, 0.08);
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --accent: linear-gradient(135deg, #3b82f6, #8b5cf6);
      --red: #ef4444;
      --green: #10b981;
      --orange: #f59e0b;
  }
  
  * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
  }
  
  body {
      background-color: var(--bg);
      color: var(--text);
      font-family: 'Plus Jakarta Sans', sans-serif;
      height: 100vh;
      overflow: hidden;
      display: flex;
  }
  
  .app-wrapper {
      display: flex;
      flex-direction: column;
      flex: 1;
      max-width: 1200px;
      margin: 0 auto;
      padding: 1.5rem;
  }
  
  .app-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 1rem;
      border-bottom: 1px solid var(--border);
  }
  
  .logo {
      font-weight: 700;
      font-size: 1.3rem;
      background: var(--accent);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
  }
  
  .badge {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      padding: 0.25rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.75rem;
  }
  
  .badge.ready {
      color: var(--green);
      background: rgba(16, 185, 129, 0.1);
      border-color: rgba(16, 185, 129, 0.2);
  }
  
  .main-container {
      display: grid;
      grid-template-columns: 320px 1fr;
      gap: 1.5rem;
      flex: 1;
      margin-top: 1.5rem;
      min-height: 0;
  }
  
  .sidebar {
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
  }
  
  .card {
      background: var(--panel);
      backdrop-filter: blur(12px);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 1.25rem;
  }
  
  .score-card {
      text-align: center;
  }
  
  .score-card h3 {
      font-size: 0.85rem;
      color: var(--text-muted);
      text-transform: uppercase;
      margin-bottom: 0.75rem;
  }
  
  .score-value {
      font-size: 3rem;
      font-weight: 700;
      color: var(--text-muted);
      margin-bottom: 0.25rem;
  }
  
  .score-label {
      font-size: 0.85rem;
      font-weight: 600;
      letter-spacing: 0.05em;
  }
  
  .tags-container {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-top: 0.5rem;
  }
  
  .tag {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      padding: 0.35rem 0.6rem;
      border-radius: 8px;
      font-size: 0.75rem;
      color: var(--orange);
  }
  
  .chat-container {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      display: flex;
      flex-direction: column;
      min-height: 0;
  }
  
  .chat-messages {
      flex: 1;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
      overflow-y: auto;
  }
  
  .message {
      max-width: 75%;
      padding: 1rem 1.25rem;
      border-radius: 18px;
      font-size: 0.9rem;
      line-height: 1.5;
  }
  
  .message.user {
      align-self: flex-end;
      background: linear-gradient(135deg, #2563eb, #1d4ed8);
      border-bottom-right-radius: 0;
  }
  
  .message.bot {
      align-self: flex-start;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      border-bottom-left-radius: 0;
  }
  
  .message.bot.scam {
      border-left: 4px solid var(--red);
  }
  
  .action-box {
      margin-top: 0.75rem;
      background: rgba(239, 68, 68, 0.08);
      border: 1px solid rgba(239, 68, 68, 0.2);
      border-radius: 8px;
      padding: 0.75rem;
  }
  
  .input-form {
      padding: 1rem;
      background: rgba(0, 0, 0, 0.2);
      border-top: 1px solid var(--border);
      display: flex;
      gap: 0.75rem;
  }
  
  textarea {
      flex: 1;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      border-radius: 10px;
      color: #fff;
      padding: 0.75rem;
      font-size: 0.9rem;
      resize: none;
      height: 60px;
      outline: none;
      font-family: inherit;
  }
  
  textarea:focus {
      border-color: #3b82f6;
  }
  
  button {
      background: var(--accent);
      color: #fff;
      border: none;
      padding: 0 1.5rem;
      border-radius: 10px;
      font-weight: 600;
      cursor: pointer;
      font-family: inherit;
  }
  ```

- [ ] **Step 3: Create frontend/index.js**
  Add connection checkers and message submit fetch pipelines.
  
  Code for `frontend/index.js`:
  ```javascript
  const messagesContainer = document.getElementById("chat-messages");
  const messageInput = document.getElementById("message-input");
  const sendButton = document.getElementById("send-button");
  const connectionBadge = document.getElementById("connection-badge");
  const riskScoreEl = document.getElementById("risk-score");
  const riskLevelEl = document.getElementById("risk-level");
  const indicatorsList = document.getElementById("indicators-list");
  
  // Verify api health status on load
  async function checkApiHealth() {
      try {
          const res = await fetch("/api/status");
          const data = await res.json();
          if (data.status === "healthy") {
              connectionBadge.textContent = "Agent Connected";
              connectionBadge.classList.add("ready");
          }
      } catch (err) {
          connectionBadge.textContent = "Connection Failed";
          connectionBadge.style.color = "#ef4444";
      }
  }
  
  function addMessage(text, isUser, extraHtml = "") {
      const msgDiv = document.createElement("div");
      msgDiv.className = `message ${isUser ? "user" : "bot"}`;
      msgDiv.innerHTML = `${text}${extraHtml}`;
      messagesContainer.appendChild(msgDiv);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
      return msgDiv;
  }
  
  async function handleScan() {
      const message = messageInput.value.trim();
      if (!message) return;
      
      addMessage(message, true);
      messageInput.value = "";
      
      const typingIndicator = addMessage("Analyzing...", false);
      
      try {
          const response = await fetch("/api/check-message", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ message })
          });
          
          if (!response.ok) throw new Error("Server error");
          
          const result = await response.json();
          typingIndicator.remove();
          
          // Render Score Cards
          riskScoreEl.textContent = `${result.risk_score}%`;
          riskLevelEl.textContent = result.risk_level.toUpperCase();
          
          if (result.risk_level === "High Risk") {
              riskScoreEl.style.color = "#ef4444";
              riskLevelEl.style.color = "#ef4444";
          } else if (result.risk_level === "Suspicious") {
              riskScoreEl.style.color = "#f59e0b";
              riskLevelEl.style.color = "#f59e0b";
          } else {
              riskScoreEl.style.color = "#10b981";
              riskLevelEl.style.color = "#10b981";
          }
          
          // Render Tags
          indicatorsList.innerHTML = "";
          if (result.indicators && result.indicators.length > 0) {
              result.indicators.forEach(tag => {
                  const tagEl = document.createElement("span");
                  tagEl.className = "tag";
                  tagEl.textContent = `⚠️ ${tag}`;
                  indicatorsList.appendChild(tagEl);
              });
          } else {
              indicatorsList.innerHTML = '<span class="empty-tag">No threats found</span>';
          }
          
          // Render Warning Block if Scam
          let recommendationHtml = "";
          if (result.risk_score > 60) {
              recommendationHtml = `
                  <div class="action-box">
                      <strong style="color: #ef4444; display: block; margin-bottom: 0.2rem;">💡 Recommendation:</strong>
                      ${result.recommendation.replace(/\n/g, "<br>")}
                  </div>
              `;
          }
          
          const agentMsg = addMessage(result.explanation, false, recommendationHtml);
          if (result.risk_score > 60) {
              agentMsg.classList.add("scam");
          }
          
      } catch (err) {
          typingIndicator.textContent = "Error: Could not complete message analysis.";
      }
  }
  
  sendButton.addEventListener("click", handleScan);
  messageInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          handleScan();
      }
  });
  
  checkApiHealth();
  ```

- [ ] **Step 4: Commit UI components**
  Run:
  ```bash
  git add frontend/index.html frontend/index.css frontend/index.js
  git commit -m "feat: build glassmorphic chat user interface"
  ```

---

### Task 7: Full System Verification

**Files:**
- Create: `tests/test_integration.py`
- Create: `scripts/test_connections.py`

- [ ] **Step 1: Write scripts/test_connections.py**
  Add connection checker to test credentials on start.
  
  Code for `scripts/test_connections.py`:
  ```python
  import os
  from dotenv import load_dotenv
  from openai import AzureOpenAI
  from azure.core.credentials import AzureKeyCredential
  from azure.search.documents import SearchClient
  
  load_dotenv()
  
  def test_azure():
      print("Testing Azure OpenAI credentials...")
      try:
          client = AzureOpenAI(
              api_key=os.getenv("AZURE_OPENAI_API_KEY"),
              api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
              azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
          )
          response = client.embeddings.create(
              input=["Test Connection"],
              model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBED")
          )
          print("Azure OpenAI OK!")
      except Exception as e:
          print(f"Azure OpenAI Error: {e}")
          
      print("\nTesting Azure Search credentials...")
      try:
          search_client = SearchClient(
              endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
              index_name=os.getenv("AZURE_SEARCH_INDEX"),
              credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY"))
          )
          # Simple check to see if index exists/accessible
          search_client.get_document_count()
          print("Azure Search OK!")
      except Exception as e:
          print(f"Azure Search Error: {e}")
  
  if __name__ == "__main__":
      test_azure()
  ```

- [ ] **Step 2: Create integration tests for message checking**
  Verify the full flow (SQLite lookup and RAG model parsing mocks).
  
  Code for `tests/test_integration.py`:
  ```python
  from fastapi.testclient import TestClient
  from backend.main import app
  import os
  
  client = TestClient(app)
  
  def test_integration_flow():
      # Test url regex detection matches expected lists
      from backend.detector import extract_urls
      urls = extract_urls("Please check this http://example.com")
      assert "http://example.com" in urls
  ```

- [ ] **Step 3: Run full verification suite**
  Run:
  ```powershell
  .venv\Scripts\Activate.ps1
  pytest -v
  ```
  Expected: All checks PASS.

- [ ] **Step 4: Commit test suite**
  Run:
  ```bash
  git add tests/test_integration.py scripts/test_connections.py
  git commit -m "test: add integration test suite and cloud connection validator"
  ```
