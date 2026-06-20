from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_status_endpoint():
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@patch('backend.main.AntiScamDetector')
def test_check_message_success(mock_detector_class):
    # Reset detector global variable before running to ensure it gets instantiated
    import backend.main
    backend.main.detector = None

    mock_detector = MagicMock()
    mock_detector.analyze_message.return_value = {
        "risk_score": 15,
        "risk_level": "Low Risk",
        "explanation": "Mocked test explanation",
        "detection_source": "Azure OpenAI RAG",
        "urls_checked": [],
        "blocklisted_urls": []
    }
    mock_detector_class.return_value = mock_detector

    response = client.post("/api/check-message", json={"message": "This is a clean message"})
    assert response.status_code == 200
    assert response.json() == {
        "risk_score": 15,
        "risk_level": "Low Risk",
        "explanation": "Mocked test explanation",
        "detection_source": "Azure OpenAI RAG",
        "urls_checked": [],
        "blocklisted_urls": []
    }
    mock_detector_class.assert_called_once()
    mock_detector.analyze_message.assert_called_once_with("This is a clean message")

def test_check_message_empty():
    # Empty string
    response = client.post("/api/check-message", json={"message": ""})
    assert response.status_code == 400
    assert response.json()["detail"] == "Message cannot be empty"

    # Whitespace string
    response = client.post("/api/check-message", json={"message": "   "})
    assert response.status_code == 400
    assert response.json()["detail"] == "Message cannot be empty"

