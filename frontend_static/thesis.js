const API_URL = "http://localhost:8000";

// Global references
let companySelect = null;
let loader = null;
let thesisResult = null;
let thesisSummary = null;
let debugLog = null;

function log(msg) {
    console.log(msg);
    if (debugLog) {
        debugLog.innerHTML += msg + "\n";
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Initialize references
    companySelect = document.getElementById('companySelect');
    loader = document.getElementById('loader');
    thesisResult = document.getElementById('thesisResult');
    thesisSummary = document.getElementById('thesisSummary'); // Now inside .premium-summary-box
    debugLog = document.getElementById('debug-log');

    log("DOM fully loaded");

    if (companySelect) {
        companySelect.addEventListener('change', () => {
            const company = companySelect.value;
            if (company) {
                analyzeThesis(company);
            }
        });
    }

    // Initialize other components
    fetchFearAndGreed();
});

async function analyzeThesis(company) {
    if (!company) return;

    // UI Reset
    if (thesisResult) thesisResult.style.display = 'none';
    if (loader) loader.style.display = 'flex';

    try {
        const response = await fetch(`${API_URL}/analyze-thesis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company })
        });

        const data = await response.json();

        if (data.error) {
            alert("Error: " + data.error);
            return;
        }

        renderThesis(data);

    } catch (error) {
        console.error("Fetch error:", error);
        alert("Failed to analyze thesis.");
    } finally {
        if (loader) loader.style.display = 'none';
    }
}

function renderThesis(data) {
    if (thesisResult) thesisResult.style.display = 'block';

    // 1. Render Summary (Right Column)
    if (thesisSummary) {
        // Format the summary text to be more "premium"
        // We'll assume the backend sends markdown-like text or plain text.
        // Let's wrap paragraphs and lists if possible, or just use the raw text with better CSS.
        // For now, simple replacement of newlines to breaks, but CSS will handle justification.

        // If the data is just a blob of text, we can try to make it look better.
        // But the CSS .premium-summary-box handles the typography.
        thesisSummary.innerHTML = data.summary.replace(/\n/g, '<br><br>');
    }

    // 2. Render Premium Chart (Left Column)
    const fin = data.financial_data;

    // We use Net Income as a proxy for "Intrinsic Value Projection" as per plan
    if (fin.net_income && fin.net_income.years && fin.net_income.values) {

        const trace1 = {
            x: fin.net_income.years,
            y: fin.net_income.values,
            type: 'scatter',
            mode: 'lines',
            fill: 'tozeroy', // Gradient fill effect
            line: {
                color: '#3b82f6', // Blue accent
                width: 4,
                shape: 'spline' // Smooth curves
            },
            fillcolor: {
                type: 'linear',
                x0: 0,
                y0: 0,
                x1: 0,
                y1: 1,
                colorStops: [
                    { offset: 0, color: 'rgba(59, 130, 246, 0.0)' },
                    { offset: 1, color: 'rgba(59, 130, 246, 0.3)' }
                ]
            },
            name: 'Projected Value'
        };

        const layout = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            margin: { l: 40, r: 20, t: 20, b: 40 },
            showlegend: false,
            xaxis: {
                showgrid: true,
                gridcolor: 'rgba(255, 255, 255, 0.05)',
                tickfont: { color: '#a1a1aa', family: 'Inter' },
                zeroline: false
            },
            yaxis: {
                showgrid: true,
                gridcolor: 'rgba(255, 255, 255, 0.05)',
                tickfont: { color: '#a1a1aa', family: 'Inter' },
                zeroline: false
            },
            hovermode: 'x unified',
            hoverlabel: {
                bgcolor: '#18181b',
                bordercolor: '#3b82f6',
                font: { family: 'Inter', color: '#fff' }
            }
        };

        const config = { responsive: true, displayModeBar: false };

        Plotly.newPlot('premiumChart', [trace1], layout, config);
    }
}

// Fetch Fear & Greed Index (Kept as is)
async function fetchFearAndGreed() {
    const card = document.getElementById('fearGreedCard');
    const valueEl = document.getElementById('fearGreedValue');
    const labelEl = document.getElementById('fearGreedLabel');
    const barEl = document.getElementById('fearGreedBar');

    if (!card || !valueEl || !labelEl || !barEl) return;

    try {
        const response = await fetch('/fear-and-greed');
        const data = await response.json();

        if (data.error) return;

        card.style.display = 'block';
        valueEl.textContent = data.score;
        labelEl.textContent = data.rating;
        barEl.style.width = `${data.score}%`;

        let color = '#f59e0b';
        if (data.score <= 25) color = '#ef4444';
        else if (data.score <= 45) color = '#f97316';
        else if (data.score >= 75) color = '#10b981';
        else if (data.score >= 55) color = '#3b82f6';

        valueEl.style.color = color;
        card.style.borderLeftColor = color;

    } catch (e) {
        console.error("Failed to fetch Fear & Greed:", e);
    }
}
