const SHEET_NAME = "4.Valoracion";   // <--- FIXED SHEET

// Load the sheet automatically when page loads
window.onload = () => {
    loadValoracion();
};

// Load the Valoración sheet
async function loadValoracion() {
    const res = await fetch(`http://localhost:8000/excel/sheet/${SHEET_NAME}`);
    const data = await res.json();

    renderTable(data.columns, data.rows);
}

// Apply iteration
async function applyIteration() {
    const value = document.getElementById("inputValue").value;

    const res = await fetch(
        `http://localhost:8000/excel/iterate/${SHEET_NAME}?value=${value}`,
        { method: "POST" }
    );

    const data = await res.json();
    renderTable(data.columns, data.rows);
}

// Render Excel table
function renderTable(columns, rows) {
    let html = "<table class='excel-table'><tr>";
    columns.forEach(col => html += `<th>${col}</th>`);
    html += "</tr>";

    rows.forEach(row => {
        html += "<tr>";
        columns.forEach(col => html += `<td>${row[col] ?? ""}</td>`);
        html += "</tr>";
    });

    html += "</table>";

    document.getElementById("excelTable").innerHTML = html;
}
