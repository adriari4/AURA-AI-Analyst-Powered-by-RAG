async function loadSheets() {
    const res = await fetch("http://localhost:8000/excel/sheets");
    const data = await res.json();

    const selector = document.getElementById("sheetSelect");
    selector.innerHTML = data.sheets.map(
        name => `<option value="${name}">${name}</option>`
    ).join("");

    loadSheet();
}

async function loadSheet() {
    const name = document.getElementById("sheetSelect").value;
    const res = await fetch(`http://localhost:8000/excel/sheet/${name}`);
    const data = await res.json();

    renderTable(data.columns, data.rows);
}

async function applyIteration() {
    const name = document.getElementById("sheetSelect").value;
    const value = document.getElementById("inputValue").value;

    const res = await fetch(
        `http://localhost:8000/excel/iterate/${name}?value=${value}`,
        { method: "POST" }
    );

    const data = await res.json();
    renderTable(data.columns, data.rows);
}

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

loadSheets();
