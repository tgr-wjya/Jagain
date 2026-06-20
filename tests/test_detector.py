from backend.detector import extract_urls

def test_extract_urls():
    urls = extract_urls("Click on http://scam-rewards.net/claim or go to www.link.org")
    assert "http://scam-rewards.net/claim" in urls
    assert "www.link.org" in urls
