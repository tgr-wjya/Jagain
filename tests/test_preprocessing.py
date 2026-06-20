import sqlite3
import tempfile
import os
from scripts.preprocess_urls import normalize_url, preprocess

def test_normalize_url():
    normalized, domain = normalize_url("https://www.google.com/login/")
    assert normalized == "google.com/login"
    assert domain == "google.com"
    
    normalized2, domain2 = normalize_url("http://scam-link.net/")
    assert normalized2 == "scam-link.net"
    assert domain2 == "scam-link.net"

def test_normalize_url_edge_cases():
    # Mixed case protocols and domains
    normalized, domain = normalize_url("hTTpS://WWW.Google.com/")
    assert normalized == "google.com"
    assert domain == "google.com"
    
    # Query parameters and hash fragments
    normalized, domain = normalize_url("https://example.com/path?query=val&other=1#fragment")
    assert normalized == "example.com/path"
    assert domain == "example.com"
    
    # Malformed URLs or no-scheme URLs
    normalized, domain = normalize_url("example.com")
    assert normalized == "example.com"
    assert domain == "example.com"

def test_database_schema_and_indexing():
    # Use a temporary file for SQLite DB to test setup
    fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    try:
        # Preprocess using the temp database path
        preprocess(temp_db_path)
        
        # Verify schema and indexes
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Check that table 'scam_urls' exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scam_urls';")
        table = cursor.fetchone()
        assert table is not None, "Table 'scam_urls' should exist"
        
        # Check table columns
        cursor.execute("PRAGMA table_info(scam_urls);")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        assert "id" in columns
        assert "url" in columns
        assert "domain" in columns
        assert "type" in columns
        
        # Check indexes exist on scam_urls
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='scam_urls';")
        indexes = [idx[0] for idx in cursor.fetchall()]
        assert "idx_url" in indexes, "Index 'idx_url' should exist"
        assert "idx_domain" in indexes, "Index 'idx_domain' should exist"
        
        conn.close()
    finally:
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
