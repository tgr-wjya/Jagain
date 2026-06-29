const { parseMessage, translateRiskLevel, formatReply } = require('./formatter');
const assert = require('assert');

// Test 1: Message parsing (stripping prefix)
try {
    const raw = "!jagain pinjam dulu seratus";
    const parsed = parseMessage(raw);
    assert.strictEqual(parsed, "pinjam dulu seratus");

    // Additional: non-string input
    assert.strictEqual(parseMessage(null), "");
    assert.strictEqual(parseMessage(undefined), "");
    
    // Additional: regex without trailing spaces
    assert.strictEqual(parseMessage("!jagain"), "");
    assert.strictEqual(parseMessage("!jagain   "), "");
    assert.strictEqual(parseMessage("!JAGAIN halo"), "halo");

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

    // Additional: Null/undefined defensive checks
    const formattedNull = formatReply(null);
    const expectedNull = 
`=== BOT ANTI-SCAM JAGAIN ===

Tingkat Risiko: Tidak diketahui (0%)
Indikator: Tidak ada

Penjelasan:
Tidak ada penjelasan

Rekomendasi:
Tidak ada rekomendasi`;
    assert.strictEqual(formattedNull, expectedNull);

    const formattedMissing = formatReply({ risk_level: "High Risk", risk_score: 90 });
    const expectedMissing = 
`=== BOT ANTI-SCAM JAGAIN ===

Tingkat Risiko: Risiko Tinggi (90%)
Indikator: Tidak ada

Penjelasan:
Tidak ada penjelasan

Rekomendasi:
Tidak ada rekomendasi`;
    assert.strictEqual(formattedMissing, expectedMissing);

    console.log("PASS: formatReply test");
} catch (e) {
    console.error("FAIL: formatReply test", e);
    process.exit(1);
}

console.log("All tests passed successfully!");
