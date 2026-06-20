from fastapi.testclient import TestClient
from backend.main import app
import os

client = TestClient(app)

def test_integration_flow():
    # Test url regex detection matches expected lists
    from backend.detector import extract_urls
    urls = extract_urls("Please check this http://example.com")
    assert "http://example.com" in urls
