const API_URL = "http://localhost:8000";

// --- Ticker Logic ---
async function initTicker() {
    const track = document.getElementById('tickerTrack');
    if (!track) return;

    async function updateTicker() {
        try {
            const response = await fetch(`${API_URL}/ticker`);
            const tickerData = await response.json();

            if (tickerData.error) {
                console.error("Ticker error:", tickerData.error);
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
            track.innerHTML = createItems() + createItems() + createItems() + createItems();

        } catch (error) {
            console.error("Failed to fetch ticker data:", error);
        }
    }

    // Initial load
    await updateTicker();

    // Refresh every 10 seconds
    setInterval(updateTicker, 10000);
}

// Initialize
initTicker();
