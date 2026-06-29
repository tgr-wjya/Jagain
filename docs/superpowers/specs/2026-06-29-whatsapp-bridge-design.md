# Spesifikasi Desain: WhatsApp Local Demo Bridge

Spesifikasi ini menjelaskan detail teknis dari pembuatan jembatan (bridge) WhatsApp lokal untuk Jagain Anti-Scam Chatbot.

## 1. Tujuan
Membangun jembatan penghubung antara platform WhatsApp dengan backend Python FastAPI Jagain secara lokal menggunakan pustaka `whatsapp-web.js` untuk tujuan demonstrasi langsung tanpa memerlukan pendaftaran/persetujuan API resmi dari Meta atau Twilio.

## 2. Batasan & Syarat
* **Bahasa:** Seluruh antarmuka pesan balasan WhatsApp harus menggunakan Bahasa Indonesia (tidak ada teks Bahasa Inggris pada header atau label).
* **Format:** Tidak boleh menggunakan emoji sama sekali.
* **Keamanan Sesi:** Menggunakan penyimpanan sesi lokal (`LocalAuth`) agar tidak perlu melakukan scan QR code setiap kali aplikasi dijalankan ulang.
* **Penyaringan Pesan (Trigger):** Bot hanya akan memproses pesan yang dimulai dengan prefix `!jagain `.

## 3. Arsitektur

```
[ WhatsApp App (User) ]
         │
         ▼ (Pesan: "!jagain <teks>")
[ Node.js WhatsApp Bridge (whatsapp-web.js) ]
         │
         ├─► Parsing & Pembersihan (Menghapus "!jagain ")
         │
         ▼ (POST /api/check-message)
[ Python FastAPI Backend (Uvicorn:8000) ]
         │
         ├─► SQLite Blocklist & Azure OpenAI RAG
         │
         ▼ (JSON Response)
[ Node.js WhatsApp Bridge (whatsapp-web.js) ]
         │
         ├─► Penerjemahan Label ke Bahasa Indonesia
         │
         ▼ (Pesan Balasan Tanpa Emoji)
[ WhatsApp App (User) ]
```

## 4. Struktur File
Proyek akan ditambahkan direktori baru di root workspace:
```text
/
├── whatsapp/
│   ├── package.json   # Dependensi Node.js
│   └── index.js       # Script utama jembatan WhatsApp
```

## 5. Implementasi Format Pesan (Bahasa Indonesia & No Emoji)

Format pemetaan terjemahan dari respon backend:
* `High Risk` -> `Risiko Tinggi`
* `Medium Risk` -> `Risiko Sedang`
* `Suspicious` -> `Mencurigakan`
* `Safe` -> `Aman`
* `Low Risk` -> `Risiko Rendah`

Format teks keluaran WhatsApp:
```text
=== BOT ANTI-SCAM JAGAIN ===

Tingkat Risiko: {Translated Risk Level} ({risk_score}%)
Indikator: {Translated/Mapped Indicators}

Penjelasan:
{explanation}

Rekomendasi:
{recommendation}
```

## 6. Rencana Pengujian (Manual Verification)
1. Jalankan backend Python: `python -m uvicorn backend.main:app --port 8000`
2. Jalankan jembatan WhatsApp: `cd whatsapp && node index.js`
3. Pindai QR Code yang muncul di terminal menggunakan fitur **Linked Devices** pada aplikasi WhatsApp di ponsel.
4. Kirim pesan dari ponsel lain atau ponsel sendiri: `!jagain Pinjam dulu seratus`
5. Pastikan balasan yang diterima berbentuk teks Bahasa Indonesia, tanpa emoji, dan dengan format yang sesuai.
