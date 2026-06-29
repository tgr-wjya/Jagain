const RISK_LEVEL_TRANSLATIONS = {
    "High Risk": "Risiko Tinggi",
    "Medium Risk": "Risiko Sedang",
    "Suspicious": "Mencurigakan",
    "Safe": "Aman",
    "Low Risk": "Risiko Rendah"
};

function parseMessage(text) {
    if (typeof text !== 'string') return "";
    return text.replace(/^!jagain\s*/i, "").trim();
}

function translateRiskLevel(level) {
    return RISK_LEVEL_TRANSLATIONS[level] || level;
}

function formatReply(result) {
    if (!result) {
        return [
            "=== BOT ANTI-SCAM JAGAIN ===",
            "",
            "Tingkat Risiko: Tidak diketahui (0%)",
            "Indikator: Tidak ada",
            "",
            "Penjelasan:",
            "Tidak ada penjelasan",
            "",
            "Rekomendasi:",
            "Tidak ada rekomendasi"
        ].join("\n");
    }

    const level = translateRiskLevel(result.risk_level || "Unknown");
    const score = result.risk_score !== undefined ? result.risk_score : 0;
    const indicators = result.indicators && result.indicators.length > 0
        ? result.indicators.join(", ")
        : "Tidak ada";
    
    const explanation = result.explanation || "Tidak ada penjelasan";
    const recommendation = result.recommendation || "Tidak ada rekomendasi";

    return [
        "=== BOT ANTI-SCAM JAGAIN ===",
        "",
        `Tingkat Risiko: ${level} (${score}%)`,
        `Indikator: ${indicators}`,
        "",
        "Penjelasan:",
        explanation,
        "",
        "Rekomendasi:",
        recommendation
    ].join("\n");
}

module.exports = {
    parseMessage,
    translateRiskLevel,
    formatReply
};
