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
