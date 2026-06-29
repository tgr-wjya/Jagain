# WhatsApp Local Demo Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local WhatsApp-to-FastAPI bridge using Node.js to demo the Jagain Anti-Scam Bot on a linked phone number.

**Architecture:** A standalone Node.js process using `whatsapp-web.js` connects to WhatsApp Web as a linked device. It listens for incoming/outgoing messages starting with `!jagain `, calls the running local FastAPI endpoint to analyze the text, formats the response in Indonesian with no emojis, and replies back.

**Tech Stack:** Node.js, `whatsapp-web.js` (v1.26+), `qrcode-terminal` (v0.12+), native fetch API.

---

### Task 1: Setup Node.js Environment

**Files:**
- Create: `whatsapp/package.json`

- [ ] **Step 1: Write the `package.json` configuration**

Create the file `C:\Users\Tegar Wijaya Kusuma\Documents\Uni\Semester 6\AI_ML\GenAI\Datasets\TB\whatsapp\package.json` with the following content:
```json
{
  "name": "jagain-whatsapp-bridge",
  "version": "1.0.0",
  "description": "WhatsApp Web bridge for Jagain Anti-Scam Chatbot",
  "main": "index.js",
  "type": "commonjs",
  "scripts": {
    "test": "node test_formatter.js",
    "start": "node index.js"
  },
  "dependencies": {
    "qrcode-terminal": "^0.12.0",
    "whatsapp-web.js": "^1.26.0"
  }
}
```

- [ ] **Step 2: Run npm install**

Run: `cd whatsapp && npm install`
Expected: Dependencies are installed, creating a `node_modules` folder.

- [ ] **Step 3: Commit**

Run:
```bash
git add whatsapp/package.json
git commit -m "chore: setup whatsapp folder and package.json"
```

---

### Task 2: Implement and Verify Formatter & Translation Logic (TDD)

We will write unit tests for the message parsing, translation, and rendering logic first, then implement the formatter to make them pass.

**Files:**
- Create: `whatsapp/test_formatter.js`
- Create: `whatsapp/formatter.js`

- [ ] **Step 1: Write the formatter tests**

Create `C:\Users\Tegar Wijaya Kusuma\Documents\Uni\Semester 6\AI_ML\GenAI\Datasets\TB\whatsapp\test_formatter.js` containing:
```javascript
const { parseMessage, translateRiskLevel, formatReply } = require('./formatter');
const assert = require('assert');

// Test 1: Message parsing (stripping prefix)
try {
    const raw = "!jagain pinjam dulu seratus";
    const parsed = parseMessage(raw);
    assert.strictEqual(parsed, "pinjam dulu seratus");
    console.log("PASS: parseMessage test");
} catch (e) {
    console.error("FAIL: parseMessage test", e);
    process.exit(1);
}

// Test 2: Risk Level translations
try {
    assert.strictEqual(translateRiskLevel("High Risk"), "Risiko Tinggi");
    assert.strictEqual(translateRiskLevel("Medium Risk"), "Risiko Sedang");
    assert.strictEqual(translateRiskLevel("Suspicious"), "Mencurigakan");
    assert.strictEqual(translateRiskLevel("Safe"), "Aman");
    assert.strictEqual(translateRiskLevel("Low Risk"), "Risiko Rendah");
    console.log("PASS: translateRiskLevel test");
} catch (e) {
    console.error("FAIL: translateRiskLevel test", e);
    process.exit(1);
}

// Test 3: Formatting output format (No Emojis & Indonesian)
try {
    const mockResult = {
        risk_score: 100,
        risk_level: "High Risk",
        indicators: ["Blacklisted URL link"],
        explanation: "Pesan mengandung link phishing yang berbahaya.",
        recommendation: "Jangan klik link tersebut."
    };
    const formatted = formatReply(mockResult);
    const expected = 
`=== BOT ANTI-SCAM JAGAIN ===

Tingkat Risiko: Risiko Tinggi (100%)
Indikator: Blacklisted URL link

Penjelasan:
Pesan mengandung link phishing yang berbahaya.

Rekomendasi:
Jangan klik link tersebut.`;

    assert.strictEqual(formatted, expected);
    console.log("PASS: formatReply test");
} catch (e) {
    console.error("FAIL: formatReply test", e);
    process.exit(1);
}

console.log("All tests passed successfully!");
```

- [ ] **Step 2: Run the test to ensure it fails**

Run: `node whatsapp/test_formatter.js`
Expected: FAIL (Cannot find module './formatter')

- [ ] **Step 3: Write minimal implementation of `formatter.js`**

Create `C:\Users\Tegar Wijaya Kusuma\Documents\Uni\Semester 6\AI_ML\GenAI\Datasets\TB\whatsapp\formatter.js` containing:
```javascript
function parseMessage(text) {
    if (!text) return "";
    return text.replace(/^!jagain\s+/i, "").trim();
}

function translateRiskLevel(level) {
    const translations = {
        "High Risk": "Risiko Tinggi",
        "Medium Risk": "Risiko Sedang",
        "Suspicious": "Mencurigakan",
        "Safe": "Aman",
        "Low Risk": "Risiko Rendah"
    };
    return translations[level] || level;
}

function formatReply(result) {
    const level = translateRiskLevel(result.risk_level);
    const score = result.risk_score;
    const indicators = result.indicators && result.indicators.length > 0
        ? result.indicators.join(", ")
        : "Tidak ada";
    
    return [
        "=== BOT ANTI-SCAM JAGAIN ===",
        "",
        `Tingkat Risiko: ${level} (${score}%)`,
        `Indikator: ${indicators}`,
        "",
        "Penjelasan:",
        result.explanation,
        "",
        "Rekomendasi:",
        result.recommendation
    ].join("\n");
}

module.exports = {
    parseMessage,
    translateRiskLevel,
    formatReply
};
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `node whatsapp/test_formatter.js`
Expected: PASS ("All tests passed successfully!")

- [ ] **Step 5: Commit**

Run:
```bash
git add whatsapp/test_formatter.js whatsapp/formatter.js
git commit -m "feat: implement and verify message formatter and translation"
```

---

### Task 3: Implement WhatsApp Client Logic

**Files:**
- Create: `whatsapp/index.js`

- [ ] **Step 1: Write `index.js` with client initialization and event handlers**

Create `C:\Users\Tegar Wijaya Kusuma\Documents\Uni\Semester 6\AI_ML\GenAI\Datasets\TB\whatsapp\index.js` containing:
```javascript
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const { parseMessage, formatReply } = require('./formatter');

const BACKEND_URL = "http://127.0.0.1:8000/api/check-message";

// Initialize client with local persistence and headless browser options
const client = new Client({
    authStrategy: new LocalAuth({
        dataPath: './.wwebjs_auth'
    }),
    puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

// Generate QR Code
client.on('qr', (qr) => {
    console.log('Scan the QR code below to connect to WhatsApp:');
    qrcode.generate(qr, { small: true });
});

// Client ready
client.on('ready', () => {
    console.log('Jagain WhatsApp Bridge is ready!');
});

// Handle incoming and outgoing messages (triggers when you send a message too)
client.on('message_create', async (msg) => {
    if (!msg.body) return;
    
    // Check if the message starts with !jagain prefix
    if (msg.body.toLowerCase().startsWith('!jagain ')) {
        const rawText = parseMessage(msg.body);
        if (!rawText) return;
        
        console.log(`Processing message: "${rawText}" from: ${msg.from}`);
        
        try {
            // Call FastAPI backend
            const response = await fetch(BACKEND_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message: rawText })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            // Format response and send reply
            const replyText = formatReply(result);
            await msg.reply(replyText);
            console.log(`Successfully replied to: ${msg.from}`);
        } catch (error) {
            console.error(`Failed to analyze message or send reply: ${error.message}`);
            // Fallback response in Indonesian with no emojis
            const fallbackText = [
                "=== BOT ANTI-SCAM JAGAIN ===",
                "",
                "Terjadi kesalahan saat memproses analisis pesan.",
                "Silakan coba lagi beberapa saat lagi."
            ].join("\n");
            await msg.reply(fallbackText);
        }
    }
});

client.initialize();
```

- [ ] **Step 2: Commit**

Run:
```bash
git add whatsapp/index.js
git commit -m "feat: implement whatsapp client and API connection"
```
