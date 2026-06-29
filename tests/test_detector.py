from unittest.mock import patch, MagicMock, ANY
from backend.detector import extract_urls, AntiScamDetector

def test_extract_urls():
    urls = extract_urls("Click on http://scam-rewards.net/claim or go to www.link.org")
    assert "http://scam-rewards.net/claim" in urls
    assert "www.link.org" in urls

@patch('backend.detector.AzureKeyCredential')
@patch('backend.detector.AzureOpenAI')
@patch('backend.detector.SearchClient')
@patch('backend.detector.check_url_in_db')
def test_analyze_message_phishing_short_circuit(mock_check_db, mock_search_client, mock_openai_client, mock_credential):
    # Setup mock check_url_in_db to return "phishing" for a specific url
    mock_check_db.return_value = "phishing"
    
    # Instantiate detector
    detector = AntiScamDetector()
    
    # Run analyze_message
    message = "Go to http://bad-link.com now!"
    result = detector.analyze_message(message)
    
    # Assert check_url_in_db was called
    mock_check_db.assert_called_with("http://bad-link.com", conn=ANY)
    
    # Assert RAG and OpenAI were NOT called
    detector.openai_client.embeddings.create.assert_not_called()
    detector.search_client.search.assert_not_called()
    detector.openai_client.chat.completions.create.assert_not_called()
    
    # Assert correct response structure and content
    assert result["risk_score"] == 100
    assert result["risk_level"] == "High Risk"
    assert result["detection_source"] == "SQLite Blocklist"
    assert "bad-link.com" in result["explanation"]
    assert result["urls_checked"] == ["http://bad-link.com"]
    assert result["blocklisted_urls"] == ["http://bad-link.com"]

@patch('backend.detector.AzureKeyCredential')
@patch('backend.detector.AzureOpenAI')
@patch('backend.detector.SearchClient')
@patch('backend.detector.check_url_in_db')
def test_analyze_message_regular_flow(mock_check_db, mock_search_client, mock_openai_client, mock_credential):
    # Setup mock check_url_in_db to return None (no blocklisted urls)
    mock_check_db.return_value = None
    
    # Mock search client results
    mock_search = MagicMock()
    mock_search.search.return_value = [
        {"text": "historical scam message", "label": "phishing"},
        {"text": "good message", "label": "legitimate"}
    ]
    
    # Mock embedding creation
    mock_embeddings = MagicMock()
    mock_embeddings.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
    mock_openai = MagicMock()
    mock_openai.embeddings.create.return_value = mock_embeddings
    
    # Mock completions creation returning a JSON response
    mock_choice = MagicMock()
    mock_choice.message.content = '{"risk_score": 10, "risk_level": "Low Risk", "indicators": [], "explanation": "Looks safe", "recommendation": "None"}'
    mock_openai.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
    
    # Assign the mock clients to be returned by patched AzureOpenAI and SearchClient
    mock_openai_client.return_value = mock_openai
    mock_search_client.return_value = mock_search
    
    detector = AntiScamDetector()
    
    # Run analyze_message
    message = "Hello, how are you?"
    result = detector.analyze_message(message)
    
    # Verify mock calls
    mock_openai.embeddings.create.assert_called_once()
    mock_search.search.assert_called_once()
    mock_openai.chat.completions.create.assert_called_once()
    
    # Verify result fields
    assert result["risk_score"] == 10
    assert result["risk_level"] == "Low Risk"
    assert result["detection_source"] == "Azure OpenAI RAG"
    assert result["urls_checked"] == []
    assert result["blocklisted_urls"] == []

@patch('backend.detector.AzureKeyCredential')
@patch('backend.detector.AzureOpenAI')
@patch('backend.detector.SearchClient')
@patch('backend.detector.check_url_in_db')
def test_analyze_message_openai_failure_fallback(mock_check_db, mock_search_client, mock_openai_client, mock_credential):
    mock_check_db.return_value = None
    
    mock_search = MagicMock()
    mock_search.search.return_value = []
    
    mock_embeddings = MagicMock()
    mock_embeddings.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
    mock_openai = MagicMock()
    mock_openai.embeddings.create.return_value = mock_embeddings
    
    # Mock completions API failure
    mock_openai.chat.completions.create.side_effect = Exception("API connection timed out")
    
    mock_openai_client.return_value = mock_openai
    mock_search_client.return_value = mock_search
    
    detector = AntiScamDetector()
    result = detector.analyze_message("Hello there")
    
    # Verify result fields are set to fallback values
    assert result["risk_score"] == 50
    assert result["risk_level"] == "Suspicious"
    assert "API connection timed out" in result["explanation"]
    assert result["detection_source"] == "Azure OpenAI RAG"

@patch('backend.detector.AzureKeyCredential')
@patch('backend.detector.AzureOpenAI')
@patch('backend.detector.SearchClient')
@patch('backend.detector.check_url_in_db')
def test_analyze_message_routing(mock_check_db, mock_search_client, mock_openai_client, mock_credential):
    mock_check_db.return_value = None
    
    mock_search = MagicMock()
    mock_search.search.return_value = []
    
    mock_embeddings = MagicMock()
    mock_embeddings.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
    mock_openai = MagicMock()
    mock_openai.embeddings.create.return_value = mock_embeddings
    
    mock_choice = MagicMock()
    mock_choice.message.content = '{"risk_score": 10, "risk_level": "Low Risk", "indicators": [], "explanation": "Safe", "recommendation": "None"}'
    mock_completions = MagicMock()
    mock_completions.choices = [mock_choice]
    mock_completions.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    mock_openai.chat.completions.create.return_value = mock_completions
    
    mock_openai_client.return_value = mock_openai
    mock_search_client.return_value = mock_search
    
    with patch.dict('os.environ', {
        'AZURE_OPENAI_DEPLOYMENT_CHAT': 'gpt-4o',
        'AZURE_OPENAI_DEPLOYMENT_CHAT_MINI': 'gpt-5.4-mini'
    }):
        detector = AntiScamDetector()
        
        # Test routing short message
        short_message = "Short msg"
        detector.analyze_message(short_message)
        mock_openai.chat.completions.create.assert_any_call(
            model='gpt-5.4-mini',
            response_format={"type": "json_object"},
            messages=ANY
        )
        
        # Test routing long message
        long_message = "A" * 200
        detector.analyze_message(long_message)
        mock_openai.chat.completions.create.assert_any_call(
            model='gpt-4o',
            response_format={"type": "json_object"},
            messages=ANY
        )
