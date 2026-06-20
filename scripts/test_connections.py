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
