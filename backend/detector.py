import os
import re
import json
import sqlite3
from dotenv import load_dotenv
load_dotenv()

from openai import AzureOpenAI
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
            conn = None
            try:
                with sqlite3.connect(DB_PATH) as c:
                    conn = c
                    for url in urls:
                        status = check_url_in_db(url, conn=conn)
                        if status == "phishing":
                            phishing_urls.append(url)
            finally:
                if conn is not None:
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
        """.strip()
        
        try:
            response = self.openai_client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT"),
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt.replace("{context}", context)},
                    {"role": "user", "content": message}
                ]
            )
            result = json.loads(response.choices[0].message.content)
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
