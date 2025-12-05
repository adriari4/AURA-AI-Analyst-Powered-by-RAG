window.onload = () => {
    loadCompanies();
    // Default load
    loadThesis("NVIDIA");
};

const API_BASE = "http://localhost:8000";
let chartInstance = null;

/* ----------------------------------------
   LOAD COMPANIES LIST
---------------------------------------- */
/* ----------------------------------------
   LOAD COMPANIES LIST
---------------------------------------- */
async function loadCompanies() {
    const listContainer = document.getElementById("companyList");
    try {
        const res = await fetch(`${API_BASE}/companies`);
        const data = await res.json();

        listContainer.innerHTML = "";

        data.companies.forEach(company => {
            const btn = document.createElement("button");
            btn.className = "company-btn";
            btn.textContent = company;

            // Set initial active state
            if (company === "NVIDIA" || company === "NVIDIA_Thesis_INVESTMENT") {
                btn.classList.add("active");
            }

            btn.addEventListener("click", () => {
                // Update Title
                document.getElementById("companyTitle").textContent = company;

                // Update Active State
                document.querySelectorAll(".company-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");

                // Load Data
                loadThesis(company);
            });

            listContainer.appendChild(btn);
        });

    } catch (err) {
        console.error("Failed to load companies:", err);
    }
}

/* ----------------------------------------
   LOAD THESIS (Summary + Chart)
---------------------------------------- */
async function loadThesis(companyName) {
    loadSummary(companyName);
    loadChart(companyName);
}

/* ----------------------------------------
   LOAD SUMMARY
---------------------------------------- */
async function loadSummary(companyName) {
    const box = document.getElementById("summary-content");
    box.innerHTML = "<div style='padding:20px; text-align:center; color:#666;'>Loading analysis for " + companyName + "...</div>";

    try {
        // Use the new generic endpoint
        const res = await fetch(`${API_BASE}/companies/${companyName}/summary`);
        if (!res.ok) throw new Error("Failed to fetch summary");

        const data = await res.json();
        box.innerHTML = data.summary;
    } catch (err) {
        box.textContent = "Failed to load summary. Please ensure the PDF exists in data/pdfs.";
        console.error(err);
    }
}

/* ----------------------------------------
   LOAD CHART
---------------------------------------- */
async function loadChart(companyName) {
    try {
        const res = await fetch(`${API_BASE}/companies/${companyName}/chart`);
        const data = await res.json();

        const ctx = document.getElementById("chartCanvas").getContext("2d");

        // Destroy previous chart if exists
        if (chartInstance) {
            chartInstance.destroy();
        }

        // Create Gradient
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, "rgba(78, 168, 255, 0.5)"); // Top: Blue
        gradient.addColorStop(1, "rgba(78, 168, 255, 0.0)"); // Bottom: Transparent

        chartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels: data.years,
                datasets: [
                    {
                        label: "Intrinsic Value (EV/FCF)",
                        data: data.intrinsic_values,
                        borderColor: "#4ea8ff",
                        backgroundColor: gradient,
                        borderWidth: 3,
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: "#18181b",
                        pointBorderColor: "#4ea8ff",
                        pointBorderWidth: 2,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        pointHoverBackgroundColor: "#4ea8ff",
                        pointHoverBorderColor: "#fff"
                    },
                    {
                        label: "Current Price",
                        data: data.current_price,
                        borderColor: "#f6c23e",
                        borderDash: [6, 6],
                        borderWidth: 2,
                        tension: 0.4,
                        pointRadius: 0,
                        pointHoverRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end',
                        labels: {
                            color: "#a1a1aa",
                            usePointStyle: true,
                            boxWidth: 8,
                            font: { family: "Inter", size: 12, weight: 500 }
                        }
                    },
                    title: {
                        display: true,
                        text: data.title,
                        align: 'start',
                        color: "#f4f4f5",
                        font: { family: "Montserrat", size: 18, weight: 600 },
                        padding: { bottom: 20 }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(24, 24, 27, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#a1a1aa',
                        borderColor: '#3f3f46',
                        borderWidth: 1,
                        padding: 10,
                        displayColors: true,
                        callbacks: {
                            label: function (context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(context.parsed.y);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        },
                        ticks: {
                            color: "#71717a",
                            font: { family: "Inter", size: 12 }
                        }
                    },
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: "rgba(255,255,255,0.05)",
                            drawBorder: false
                        },
                        ticks: {
                            color: "#71717a",
                            font: { family: "Inter", size: 12 },
                            callback: function (value) {
                                return '$' + value;
                            }
                        },
                        border: { display: false }
                    }
                }
            }
        });

    } catch (err) {
        console.error("Chart load error:", err);
    }
}
