import sqlite3
from scripts.preprocess_urls import normalize_url

DB_PATH = "scam_urls.db"

TRUSTED_DOMAINS = {
    "google.com", "drive.google.com", "docs.google.com", "github.com",
    "wa.me", "t.me", "telegram.me", "facebook.com", "instagram.com",
    "youtube.com", "dropbox.com", "microsoft.com", "apple.com",
    "twitter.com", "x.com"
}

def check_url_in_db(raw_url, conn=None):
    normalized, domain = normalize_url(raw_url)
    
    if conn is not None:
        return _query_db(conn, normalized, domain)
        
    conn = None
    try:
        with sqlite3.connect(DB_PATH) as c:
            conn = c
            return _query_db(conn, normalized, domain)
    finally:
        if conn is not None:
            conn.close()

def _query_db(conn, normalized, domain):
    cursor = conn.cursor()
    
    # Exact match check
    cursor.execute("SELECT type FROM scam_urls WHERE url = ?", (normalized,))
    row = cursor.fetchone()
    if row:
        return row[0]
        
    # Domain match check (skip if the domain is a trusted domain)
    if domain and domain not in TRUSTED_DOMAINS:
        cursor.execute("SELECT type FROM scam_urls WHERE domain = ?", (domain,))
        row = cursor.fetchone()
        if row:
            return row[0]
            
    return None
