const API_URL = ""; // Use relative path

// --- Ticker Logic ---
async function initTicker() {
    console.log("Ticker: Initializing...");
    const track = document.getElementById('tickerTrack');
    if (!track) {
        console.error("Ticker: Track element not found");
        return;
    }

    async function updateTicker() {
        try {
            console.log("Ticker: Fetching data...");
            // Use relative path /ticker
            const response = await fetch(`${API_URL}/ticker`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const tickerData = await response.json();
            console.log("Ticker: Data received", tickerData);

            if (tickerData.error) {
                console.error("Ticker: API error:", tickerData.error);
                return;
            }

            if (!tickerData || tickerData.length === 0) {
                console.warn("Ticker: No data received");
                return;
            }

            // Create items HTML
            const createItems = () => tickerData.map(item => `
                <div class="ticker-item">
                    <span style="font-weight:700; color:#fff;">${item.symbol}</span> 
                    ${item.price} 
                    <span class="${item.up ? 'up' : 'down'}">
                        ${item.up ? '▲' : '▼'} ${item.change}
                    </span>
                </div>
            `).join('');

            // Duplicate content enough times to fill screen + buffer for smooth loop
            // We create 4 sets of data to ensure the track is long enough
            const itemsHtml = createItems();
            track.innerHTML = itemsHtml + itemsHtml + itemsHtml + itemsHtml;
            console.log("Ticker: Updated DOM");

        } catch (error) {
            console.error("Ticker: Failed to fetch data:", error);
        }
    }

    // Initial load
    await updateTicker();

    // Refresh every 60 seconds
    setInterval(updateTicker, 60000);
}

// Initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTicker);
} else {
    initTicker();
}
