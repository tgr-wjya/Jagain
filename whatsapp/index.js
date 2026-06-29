const path = require('path');
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const { parseMessage, formatReply } = require('./formatter');

const BACKEND_URL = "http://127.0.0.1:8000/api/check-message";

// Initialize client with local persistence and headless browser options
const client = new Client({
    authStrategy: new LocalAuth({
        dataPath: path.join(__dirname, '.wwebjs_auth')
    }),
    puppeteer: {
        executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
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
    if (msg.body.toLowerCase().startsWith('!jagain')) {
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
