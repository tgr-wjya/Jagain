# Spesifikasi Desain: Jagain (Multilingual Anti-Scam Chatbot)

Dokumen ini mendokumentasikan spesifikasi teknis dan desain arsitektur untuk proyek agen chatbot anti-scam bernama **Jagain**. Chatbot ini dirancang untuk mendeteksi penipuan dalam pesan teks (SMS/chat) serta tautan (URL) menggunakan metode hibrida: basis data URL lokal (SQLite) dan Retrieval-Augmented Generation (RAG) berbasis Microsoft AI Foundry (Azure OpenAI gpt-4o dan Azure AI Search).

## 1. Arsitektur Sistem (High-Level Architecture)

Aplikasi didekomposisi menjadi 4 komponen utama:
1. **Engine Preprocessing Data (Lokal & Offline):**
   - Mengubah dataset mentah menjadi format siap pakai.
   - Memasukkan URL berbahaya/aman ke basis data SQLite lokal.
   - Meng-embed pesan SMS Spam Collection dan mengunggahnya ke Azure AI Search.
2. **Script Deployment Azure:**
   - Script PowerShell (`deploy_azure.ps1`) menggunakan Azure CLI untuk membuat grup sumber daya, mengonfigurasi Azure OpenAI, men-deploy model (`gpt-4o` dan `text-embedding-3-small`), membuat Azure AI Search, dan memproduksi file `.env`.
3. **Backend Service (Python FastAPI):**
   - Menangani routing logika pendeteksian.
   - Mengekstrak URL menggunakan RegEx dan mencocokkannya dengan SQLite blocklist.
   - Melakukan embedding kueri teks dan memanggil Azure AI Search jika lolos deteksi URL cepat.
   - Menghubungkan konteks ke Azure OpenAI (gpt-4o) untuk menghasilkan penjelasan keamanan yang interaktif dalam bahasa kueri user.
4. **Static Web App (Frontend UI):**
   - Antarmuka chat modern dengan estetika dark mode premium dan glassmorphism.
   - Indikator tingkat risiko visual dan daftar indikator kecurigaan.

---

## 2. Alur Deteksi Berurutan (Sequential Screening Flow)

Untuk meminimalisir latensi dan menekan biaya API Azure OpenAI, backend memproses kueri masukan user dengan alur berurutan berikut:

```
[User Input] 
     │
     ▼
[Regex URL Extraction]
     │
     ├─► Ada URL? ──► [Query SQLite scam_urls]
     │                      │
     │                      ├─► Ditemukan (Phishing)? ──► [Short-Circuit WARNING] (Latency <5ms, Cost $0)
     │                      │
     │                      └─► Tidak Ditemukan? ───────┐
     │                                                   ▼
     └─► Teks Saja / Lolos Cek URL ──────────────► [Embed Query & Search Azure AI Search] (150ms)
                                                         │
                                                         ▼
                                                   [Retrieve Top-K Contexts]
                                                         │
                                                         ▼
                                                   [Invoke Azure OpenAI gpt-4o] (1.5s)
                                                         │
                                                         ▼
                                                   [Structured JSON Response] (Multilingual)
```

---

## 3. Spesifikasi Skema Database & Indeks

### A. Database SQLite Lokal (`scam_urls.db`)
Digunakan untuk pencocokan URL instan (O(1)). Menggabungkan data dari `Phishing URLs.csv` dan `URL dataset.csv`.

```sql
CREATE TABLE scam_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,         -- URL yang dinormalisasi (lowercase, tanpa protokol/www)
    domain TEXT,            -- Root domain hasil ekstraksi
    type TEXT               -- 'phishing' atau 'legitimate'
);

CREATE INDEX idx_url ON scam_urls(url);
CREATE INDEX idx_domain ON scam_urls(domain);
```

### B. Azure AI Search (`sms-scams-index`)
Digunakan untuk pencarian semantik kemiripan teks menggunakan dataset `sms+spam+collection/SMSSpamCollection`.

- **Field Schema:**
  - `id`: Edm.String (Key, Retrievable)
  - `text`: Edm.String (Searchable, Retrievable)
  - `label`: Edm.String (Filterable, Retrievable) - Berisi 'spam' atau 'ham'
  - `vector`: Collection(Edm.Single) (Searchable, Dimension: 1536, Vector Search Profile: Cosine)

---

## 4. Prompt RAG & Dukungan Multilingual (Multilingual Support)

Kueri dalam bahasa apapun (misalnya Bahasa Indonesia, Inggris, Jepang, dll.) akan di-embed oleh model multilingual `text-embedding-3-small`, menyelaraskannya dengan dataset referensi SMS berbahasa Inggris di Azure AI Search secara semantik.

Sistem prompt memandu `gpt-4o` untuk mendeteksi bahasa masukan user dan membalas dalam bahasa tersebut:

```
SYSTEM PROMPT:
Anda adalah asisten keamanan anti-scam bernama Jagain. Tugas Anda adalah menganalisis pesan dari pengguna.
Gunakan konteks pesan serupa (scam/legitimate) berikut yang ditarik dari basis data kami sebagai referensi penilaian Anda:

[KONTEKS REFERENSI]
Pesan: {text} | Label: {label}
...

[PERSYARATAN UTAMA]
Deteksi bahasa yang digunakan oleh pengguna dalam pesan mereka.
1. Lakukan analisis Anda dalam bahasa yang terdeteksi tersebut.
2. Tulis isi kolom "explanation" dan "recommendation" dalam BAHASA YANG SAMA.
3. Kolom "risk_level" dan "indicators" harus tetap ditulis dalam bahasa Inggris untuk keperluan standardisasi data.

Kembalikan respon HANYA dalam format JSON seperti contoh berikut:
{
  "risk_score": 90,
  "risk_level": "High Risk",
  "indicators": ["Suspicious URL link", "Urgency claim"],
  "explanation": "[Penjelasan analisis dalam bahasa pengguna]",
  "recommendation": "[Rekomendasi tindakan dalam bahasa pengguna]"
}
```

---

## 5. Rencana Verifikasi (Verification Plan)

### A. Pengujian Otomatis
- **Unit Testing (Python pytest):**
    - Verifikasi ekstraksi RegEx URL dan fungsi normalisasi URL.
    - Verifikasi query SQLite mengembalikan nilai yang tepat untuk domain yang terdaftar/tidak terdaftar.
    - Mocking API Azure OpenAI dan Azure AI Search untuk memverifikasi parser JSON hasil respon GPT bekerja dengan baik.
- **Integration Testing:**
    - Skrip verifikasi koneksi cloud (`test_connections.py`) untuk memvalidasi konfigurasi `.env` ke Azure AI Search dan Azure OpenAI sebelum aplikasi dijalankan.

### B. Verifikasi Manual
- Menjalankan server backend FastAPI secara lokal dan mengetes endpoint `POST /api/check-message` dengan postman/curl.
- Membuka halaman frontend `Jagain` di web browser dan mencoba memasukkan pesan penipuan dalam bahasa Indonesia, Inggris, dan URL acak untuk melihat perubahan indikator risiko dan respon bahasa secara langsung.
