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
