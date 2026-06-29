def test_integration_flow():
    # Test url regex detection matches expected lists
    from backend.detector import extract_urls
    urls = extract_urls("Please check this http://example.com")
    assert "http://example.com" in urls
