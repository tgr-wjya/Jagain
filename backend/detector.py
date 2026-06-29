import os
import re
import json
import sqlite3
from dotenv import load_dotenv
load_dotenv()

import time
from openai import AzureOpenAI, RateLimitError, APIConnectionError
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from backend.database import check_url_in_db, DB_PATH

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
        # ponytail: route to mini model for short inputs
        self.deployment_chat = os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT")
        self.deployment_chat_mini = os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT_MINI", self.deployment_chat)
        
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
        if urls:
            # ponytail: try/finally for connection lifecycle
            conn = sqlite3.connect(DB_PATH)
            try:
                for url in urls:
                    if check_url_in_db(url, conn=conn) == "phishing":
                        phishing_urls.append(url)
            finally:
                conn.close()
                
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
        1. If the detected language is Indonesian (or related regional languages), perform your analysis, explanation, and recommendation in Bahasa Indonesia.
        2. Otherwise (including English and all other languages), perform your analysis, explanation, and recommendation in English.
        3. The "risk_level" and "indicators" must always remain in English for standardization.
        
        Return ONLY a JSON response in the following schema:
        {
          "risk_score": 90,
          "risk_level": "High Risk",
          "indicators": ["Suspicious URL link", "Urgency claim"],
          "explanation": "[Written in either English or Bahasa Indonesia based on the rules above]",
          "recommendation": "[Written in either English or Bahasa Indonesia based on the rules above]"
        }
        """.strip()
        
        # ponytail: select model by input length
        model = self.deployment_chat_mini if len(message) < 200 else self.deployment_chat

        try:
            # ponytail: transient errors retry logic
            for attempt in range(3):
                try:
                    response = self.openai_client.chat.completions.create(
                        model=model,
                        response_format={"type": "json_object"},
                        messages=[
                            {"role": "system", "content": system_prompt.replace("{context}", context)},
                            {"role": "user", "content": message}
                        ]
                    )
                    break
                except (RateLimitError, APIConnectionError):
                    if attempt == 2:
                        raise
                    time.sleep(2 ** attempt)

            result = json.loads(response.choices[0].message.content)
            
            # ponytail: log token usage
            if response.usage:
                print(f"[{model}] Tokens used - Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}, Total: {response.usage.total_tokens}")
        except Exception as e:
            result = {
                "risk_score": 50,
                "risk_level": "Suspicious",
                "indicators": ["API Error"],
                "explanation": f"An error occurred while analyzing the message: {str(e)}",
                "recommendation": "Please exercise caution when interacting with this message."
            }
        
        result["urls_checked"] = urls
        result["blocklisted_urls"] = []
        result["detection_source"] = "Azure OpenAI RAG"
        return result
