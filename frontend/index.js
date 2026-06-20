const messagesContainer = document.getElementById("chat-messages");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const connectionBadge = document.getElementById("connection-badge");
const riskScoreEl = document.getElementById("risk-score");
const riskLevelEl = document.getElementById("risk-level");
const indicatorsList = document.getElementById("indicators-list");

// Verify api health status on load
async function checkApiHealth() {
    try {
        const res = await fetch("/api/status");
        if (!res.ok) throw new Error("API not healthy");
        const data = await res.json();
        if (data.status === "healthy") {
            connectionBadge.textContent = "Agent Terkoneksi";
            connectionBadge.classList.remove("failed");
            connectionBadge.classList.add("ready");
        } else {
            throw new Error("Unhealthy status");
        }
    } catch (err) {
        connectionBadge.textContent = "Koneksi Gagal";
        connectionBadge.classList.remove("ready");
        connectionBadge.classList.add("failed");
    }
}

// Escapes HTML special characters to prevent XSS
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function addMessage(text, isUser, extraHtml = "") {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${isUser ? "user" : "bot"}`;
    
    if (isUser) {
        msgDiv.textContent = text;
    } else {
        msgDiv.innerHTML = `${text}${extraHtml}`;
    }
    
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return msgDiv;
}

function addTypingIndicator() {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message bot typing-message";
    msgDiv.innerHTML = `
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return msgDiv;
}

async function handleScan() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Disable inputs while scanning
    messageInput.disabled = true;
    sendButton.disabled = true;
    
    // Add user message to UI (safely escaped)
    addMessage(message, true);
    messageInput.value = "";
    
    // Add typing indicator
    const typingIndicator = addTypingIndicator();
    
    try {
        const response = await fetch("/api/check-message", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        });
        
        if (!response.ok) throw new Error("Server error");
        
        const result = await response.json();
        typingIndicator.remove();
        
        // Render Score Cards
        riskScoreEl.textContent = `${result.risk_score}%`;
        riskLevelEl.textContent = result.risk_level.toUpperCase();
        
        // Update styling based on risk level
        if (result.risk_level === "High Risk") {
            riskScoreEl.style.color = "var(--red)";
            riskLevelEl.style.color = "var(--red)";
        } else if (result.risk_level === "Suspicious") {
            riskScoreEl.style.color = "var(--orange)";
            riskLevelEl.style.color = "var(--orange)";
        } else {
            riskScoreEl.style.color = "var(--green)";
            riskLevelEl.style.color = "var(--green)";
        }
        
        // Render Tags
        indicatorsList.innerHTML = "";
        if (result.indicators && result.indicators.length > 0) {
            result.indicators.forEach(tag => {
                const tagEl = document.createElement("span");
                tagEl.className = "tag";
                tagEl.textContent = `⚠️ ${tag}`;
                indicatorsList.appendChild(tagEl);
            });
        } else {
            indicatorsList.innerHTML = '<span class="empty-tag">Tidak ada ancaman terdeteksi</span>';
        }
        
        // Render Warning Block if Scam
        let recommendationHtml = "";
        if (result.risk_score > 60) {
            recommendationHtml = `
                <div class="action-box">
                    <strong style="color: var(--red); display: block; margin-bottom: 0.4rem;">💡 Rekomendasi:</strong>
                    ${escapeHtml(result.recommendation)}
                </div>
            `;
        }
        
        const botText = escapeHtml(result.explanation);
        const agentMsg = addMessage(botText, false, recommendationHtml);
        if (result.risk_score > 60) {
            agentMsg.classList.add("scam");
        }
        
    } catch (err) {
        typingIndicator.remove();
        addMessage("Terjadi kesalahan: Tidak dapat menyelesaikan analisis pesan.", false);
    } finally {
        // Re-enable inputs
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
    }
}

sendButton.addEventListener("click", handleScan);
messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleScan();
    }
});

// Run connection check
checkApiHealth();
