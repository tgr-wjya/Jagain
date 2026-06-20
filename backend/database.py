import sqlite3
from scripts.preprocess_urls import normalize_url

DB_PATH = "scam_urls.db"

def check_url_in_db(raw_url):
    normalized, domain = normalize_url(raw_url)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Exact match check
    cursor.execute("SELECT type FROM scam_urls WHERE url = ?", (normalized,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return row[0]
        
    # Domain match check
    if domain:
        cursor.execute("SELECT type FROM scam_urls WHERE domain = ?", (domain,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return row[0]
            
    conn.close()
    return None
