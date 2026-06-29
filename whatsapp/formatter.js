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
