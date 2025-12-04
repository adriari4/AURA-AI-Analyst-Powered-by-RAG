window.onload = () => {
    loadNvidiaChart();
    loadNvidiaSummary();
};

/* ----------------------------------------
   LOAD SUMMARY FROM BACKEND
---------------------------------------- */
async function loadNvidiaSummary() {
    const box = document.getElementById("summary-content");
    box.textContent = "Loading summary…";

    try {
        const res = await fetch("http://localhost:8000/thesis/nvidia/summary");
        const data = await res.json();
        box.innerHTML = data.executive_summary;
    } catch (err) {
        box.textContent = "Failed to load summary.";
        console.error(err);
    }
}

/* ----------------------------------------
   LOAD CHART FROM BACKEND
---------------------------------------- */
async function loadNvidiaChart() {
    try {
        const res = await fetch("http://localhost:8000/thesis/nvidia/chart");
        const data = await res.json();

        const ctx = document.getElementById("chartCanvas").getContext("2d");

        // Create Gradient
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, "rgba(78, 168, 255, 0.5)"); // Top: Blue
        gradient.addColorStop(1, "rgba(78, 168, 255, 0.0)"); // Bottom: Transparent

        new Chart(ctx, {
            type: "line",
            data: {
                labels: data.years,
                datasets: [
                    {
                        label: "Intrinsic Value (EV/FCF)",
                        data: data.intrinsic_values,
                        borderColor: "#4ea8ff",
                        backgroundColor: gradient, // Use Gradient
                        borderWidth: 3,
                        tension: 0.4, // Smoother curve
                        fill: true,
                        pointBackgroundColor: "#18181b", // Dark background for point center
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
                        pointRadius: 0, // Hide points for the benchmark line
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
                        beginAtZero: false, // Let it scale to data
                        suggestedMin: 100,
                        suggestedMax: 450,
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
