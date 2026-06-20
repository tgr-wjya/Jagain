import sqlite3
from scripts.preprocess_urls import normalize_url

def test_normalize_url():
    normalized, domain = normalize_url("https://www.google.com/login/")
    assert normalized == "google.com/login"
    assert domain == "google.com"
    
    normalized2, domain2 = normalize_url("http://scam-link.net/")
    assert normalized2 == "scam-link.net"
    assert domain2 == "scam-link.net"
