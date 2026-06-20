# Design Specification: Jagain (Multilingual Anti-Scam Chatbot)

This document details the technical specifications and architectural design for the anti-scam chatbot agent named **Jagain**. The chatbot is designed to detect fraudulent messages (SMS/chat) and malicious links (URLs) using a hybrid approach: a local URL database (SQLite) and Retrieval-Augmented Generation (RAG) powered by Microsoft AI Foundry (Azure OpenAI gpt-4o and Azure AI Search).

## 1. High-Level Architecture & Components

The application is decomposed into four main components:
1. **Data Preprocessing & Ingestion Engine (Offline/Local):**
   - Prepares raw datasets for lookup and RAG.
   - Loads malicious and legitimate URLs into a local indexed SQLite database.
   - Embeds and uploads the SMS Spam Collection dataset to Azure AI Search.
2. **Azure Deployment Engine:**
   - A PowerShell script (`deploy_azure.ps1`) using Azure CLI to create resource groups, set up Azure OpenAI, deploy models (`gpt-4o` and `text-embedding-3-small`), create Azure AI Search, and output local environment secrets to a `.env` file.
3. **Backend Service (Python FastAPI):**
   - Handles the orchestration logic for scam checks.
   - Extracts URLs using RegEx and performs fast O(1) checks against the local SQLite database.
   - Generates vector embeddings for user text and retrieves matching scam history from Azure AI Search when needed.
   - Feeds contextual references to Azure OpenAI (gpt-4o) to generate interactive safety advice in the user's input language.
4. **Static Web App (Frontend UI):**
   - A premium web page featuring a modern glassmorphic chat interface.
   - Incorporates a visual "Risk Level" meter and warning indicator tags.

---

## 2. Sequential Screening Flow

To minimize latency and optimize Azure OpenAI API costs, the backend screens incoming user messages sequentially:

```
[User Input] 
     │
     ▼
[Regex URL Extraction]
     │
     ├─► URL Found? ──► [Query SQLite scam_urls]
     │                        │
     │                        ├─► Match Found (Phishing)? ──► [Short-Circuit WARNING] (Latency <5ms, Cost $0)
     │                        │
     │                        └─► No Match Found? ─────────┐
     │                                                     ▼
     └─► Text-Only / Clean URL ──────────────────► [Embed Query & Search Azure AI Search] (150ms)
                                                           │
                                                           ▼
                                                     [Retrieve Top-K Contexts]
                                                           │
                                                           ▼
                                                     [Invoke Azure OpenAI gpt-4o] (1.5s)
                                                           │
                                                           ▼
                                                     [Structured JSON Response] (Multilingual)
```

---

## 3. Database & Index Schema

### A. Local SQLite Database Schema (`scam_urls.db`)
Used for instant URL and domain checks (O(1)). Merges data from `Phishing URLs.csv` and `URL dataset.csv`.

```sql
CREATE TABLE scam_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,         -- Normalized URL (lowercase, stripped of protocol/www)
    domain TEXT,            -- Extracted root domain
    type TEXT               -- 'phishing' or 'legitimate'
);

CREATE INDEX idx_url ON scam_urls(url);
CREATE INDEX idx_domain ON scam_urls(domain);
```

### B. Azure AI Search Index (`sms-scams-index`)
Used for semantic text-similarity queries on the `sms+spam+collection/SMSSpamCollection` dataset.

- **Field Schema:**
  - `id`: Edm.String (Key, Retrievable)
  - `text`: Edm.String (Searchable, Retrievable)
  - `label`: Edm.String (Filterable, Retrievable) - Contains 'spam' or 'ham'
  - `vector`: Collection(Edm.Single) (Searchable, Dimension: 1536, Vector Search Profile: Cosine)

---

## 4. Prompt RAG & Multilingual Support

Queries in any language (e.g. Indonesian, English, Spanish, Japanese) are embedded using the multilingual `text-embedding-3-small` model, allowing semantic alignment with the English templates stored in Azure AI Search.

The system prompt instructs `gpt-4o` to detect the query language and respond in the same language:

```
SYSTEM PROMPT:
You are an expert Anti-Scam Security Assistant named Jagain. Your job is to analyze the user's message.
Use the following retrieved historical context of similar messages (scams/legitimate) to help make your decision:

[RETRIEVED CONTEXT]
Message: {text} | Label: {label}
...

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
  "explanation": "[Written in the user's input language, e.g., Indonesian/Japanese/Spanish]",
  "recommendation": "[Written in the user's input language, e.g., Indonesian/Japanese/Spanish]"
}
```

---

## 5. Verification Plan

### A. Automated Tests
- **Unit Testing (Python pytest):**
    - Verify RegEx URL extraction and normalization functions.
    - Verify SQLite queries return correct values for matched/unmatched domains.
    - Mock Azure OpenAI and Azure AI Search endpoints to verify the JSON parser handles LLM responses correctly.
- **Integration Testing:**
    - Connection testing script (`test_connections.py`) to validate local `.env` keys against the deployed cloud search and OpenAI services before spinning up the backend server.

### B. Manual Verification
- Start the FastAPI backend server and test `POST /api/check-message` using curl/Postman.
- Open the frontend page for `Jagain` in a browser, submit test messages in Indonesian and English, and verify the risk scores, indicator tags, and language responses.
