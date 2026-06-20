import os
import csv
import sqlite3
from urllib.parse import urlparse

def normalize_url(url):
    url = url.strip().lower()
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        path = parsed.path.rstrip('/')
        return f"{netloc}{path}", netloc
    except Exception:
        return url, ""

def preprocess(db_path="scam_urls.db"):
    if db_path != ":memory:" and os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE scam_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            domain TEXT,
            type TEXT
        );
        """)
        cursor.execute("CREATE INDEX idx_url ON scam_urls(url);")
        cursor.execute("CREATE INDEX idx_domain ON scam_urls(domain);")
        
        # Process Phishing URLs.csv (All phishing)
        url_file1 = r"Phishing URL dataset/Phishing URLs.csv"
        if os.path.exists(url_file1):
            with open(url_file1, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                next(reader)  # skip header
                for row in reader:
                    if not row: continue
                    normalized, domain = normalize_url(row[0])
                    try:
                        cursor.execute("INSERT INTO scam_urls (url, domain, type) VALUES (?, ?, ?)", 
                                       (normalized, domain, "phishing"))
                    except sqlite3.IntegrityError:
                        pass
                        
        # Process URL dataset.csv (phishing + legitimate)
        url_file2 = r"Phishing URL dataset/URL dataset.csv"
        if os.path.exists(url_file2):
            with open(url_file2, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                next(reader)  # skip header
                for row in reader:
                    if not row or len(row) < 2: continue
                    normalized, domain = normalize_url(row[0])
                    label = "phishing" if row[1].lower() == "phishing" else "legitimate"
                    try:
                        cursor.execute("INSERT INTO scam_urls (url, domain, type) VALUES (?, ?, ?)", 
                                       (normalized, domain, label))
                    except sqlite3.IntegrityError:
                        pass
                        
        conn.commit()
    finally:
        conn.close()
    print("SQLite preprocessing complete!")

if __name__ == "__main__":
    preprocess()
