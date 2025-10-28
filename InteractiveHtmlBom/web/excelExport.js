
function saveBomTableExcel() {
    const wb = XLSX.utils.book_new();
    const ws_data = [];
  
    // ===== Kopfbereich =====
// ===== Neuer Kopfbereich (wie im Beispielbild) =====
ws_data.push(["Projekt", "---010", "V102.0 RoHS 2\nAEC-Q Bauteile", new Date().toLocaleDateString("de-DE")]);
ws_data.push([]); // Leerzeile
ws_data.push(["Anzahl", "Name", "Typ", "Package", "Bemerkungen", "Bedarf"]);


  
    // ===== Kategorien =====
    const categoryMap = {
        R: "Widerstände",
        C: "Kondensatoren",
        D: "Dioden",
        L: "Induktivitäten",
        T: "Transistoren",
        Q: "Transistoren",
        IC: "Integrierte Schaltungen",
        U: "Integrierte Schaltungen",
        DCDC: "DCDC-Wandler",
        OK: "Optokoppler",
        LED: "Leuchtdioden",
        X: "Steckverbinder",
        J: "Steckverbinder",
        F: "Sicherungen",
        K: "Relais",
        TR: "Transformator",
        RN: "Widerstandsnetzwerk",
        M: "Motor",
        TH: "Thermistor",
        RT: "Thermistor",
        SW: "Taster / Schalter",
        B: "Batterie",
        VR: "Variable Resistor",
        TP: "Testpoint",
        MP: "Messpunkt",
        O: "Optokoppler",
        

        

      };
      
  
    // ===== Tabellenzeilen aus HTML lesen =====
    const rows = document.querySelectorAll("#bomtable.bom tbody tr");
    let currentCategory = "";
  
    rows.forEach((row) => {
      const cells = [...row.querySelectorAll("td")].map(td => td.innerText.trim());
      if (cells.length < 7) return;
  
      const ref = cells[3] || "";
      let prefix = ref.match(/^[A-Za-z]+/)?.[0]?.toUpperCase() ?? "";
      if (prefix.startsWith("VR")) prefix = "VR";
      else if (prefix.startsWith("SW")) prefix = "SW";
      else if (prefix.startsWith("LED")) prefix = "LED";
      else if (prefix.startsWith("TP")) prefix = "TP";
  
      const category = categoryMap[prefix] || "Andere";
  
      // Kategorie mit Leerzeile oben & unten
      if (category !== currentCategory) {
        ws_data.push([]);
        ws_data.push([category]);
        ws_data.push([]);
        currentCategory = category;
      }
  
      // ==== Name umbrechen nach 4 Bauteilen ====
    // ==== Name umbrechen nach 4 Bauteilen (Excel-Zeilenumbruch) ====
let refs = ref.split(",").map(x => x.trim());
let formattedRef = "";
for (let i = 0; i < refs.length; i++) {
  formattedRef += refs[i];
  if ((i + 1) % 4 === 0 && i < refs.length - 1) formattedRef += ", CHAR(10) ";
  else if (i < refs.length - 1) formattedRef += ", ";
}

// Für Excel-Zeilenumbruch aktivieren
formattedRef = formattedRef.replace(/CHAR\(10\)/g, "\n");

      // ==== Anzahl automatisch zählen ====
      const count = refs.length;
  
      const rowData = [
        count,
        formattedRef,
        cells[4] || "",
        cells[5] || "",
        "",
        ""
      ];
      ws_data.push(rowData);
  
      // ==== Border unter der Kategorie ====
      if (rows[rows.length - 1] === row || // letzte Zeile
          (rows[row.rowIndex + 1] && !ref.match(/^[A-Za-z]+/))) {
        ws_data.push([]);
      }
    });
  
    // ===== Arbeitsblatt erstellen =====
    const ws = XLSX.utils.aoa_to_sheet(ws_data);
  

/// ==== Fetter oberer & unterer Border für Kopfzeile ====
// ==== Kompletter Rahmen (oben, unten, links, rechts) für Kopfzeile ====
const headerRow = 3; // Zeile 3 enthält die Kopfzeile
const headerCols = [0, 1, 2, 3, 4, 5]; // Spalten A–F

headerCols.forEach(c => {
  const cellAddr = XLSX.utils.encode_cell({ r: headerRow - 1, c });
  if (ws[cellAddr]) {
    ws[cellAddr].s = ws[cellAddr].s || {};
    ws[cellAddr].s.border = {
      top: { style: "thick", color: { rgb: "FF000000" } },
      bottom: { style: "thick", color: { rgb: "FF000000" } },
      left: { style: "medium", color: { rgb: "FF000000" } },
      right: { style: "medium", color: { rgb: "FF000000" } },
    
    };
  }
});





    // ===== Formatierung für Kopfbereich =====
["A1", "B1", "C1", "D1"].forEach(cell => {
    if (ws[cell]) {
      ws[cell].s = {
        alignment: { horizontal: "center", vertical: "center", wrapText: true },
        font: { bold: cell === "B1" || cell === "C1", sz: 12 },
      };
    }
  });
  
    // ===== Fette Border nach jeder Kategorie =====
// ===== Jede Zelle erzeugen, damit Border sichtbar ist =====
const rangeAll = XLSX.utils.decode_range(ws['!ref']);
for (let r = rangeAll.s.r; r <= rangeAll.e.r; r++) {
  for (let c = rangeAll.s.c; c <= rangeAll.e.c; c++) {
    const addr = XLSX.utils.encode_cell({ r, c });
    if (!ws[addr]) ws[addr] = { t: "s", v: "" };
  }
}

// ===== Dünne Border für alle Werte-Zeilen unter jeder Kategorie =====
const categoryNames = Object.values(categoryMap);
let currentCategoryRow = -1;

Object.keys(ws).forEach(cell => {
  const value = ws[cell]?.v?.trim?.() || "";
  const { r } = XLSX.utils.decode_cell(cell);

  // Wenn Kategorie erkannt
  if (categoryNames.includes(value)) currentCategoryRow = r;

  // Wenn unter Kategorie und keine neue Kategorie
  if (currentCategoryRow !== -1 && r > currentCategoryRow + 1 && value !== "") {
    for (let col = 0; col < 6; col++) {
      const addr = XLSX.utils.encode_cell({ r, c: col });
      ws[addr].s = ws[addr].s || {};
      ws[addr].s.border = {
        top: { style: "thin", color: { rgb: "FF000000" } },
        bottom: { style: "thin", color: { rgb: "FF000000" } },
        left: { style: "thin", color: { rgb: "FF000000" } },
        right: { style: "thin", color: { rgb: "FF000000" } }
      };
    }
  }
});


  
  
  
    // ===== Design Header (ohne Hintergrundfarbe) =====
   // ===== Design Header (Border nur unten) =====
const headerCells = ["A5", "B5", "C5", "D5", "E5", "F5"];
headerCells.forEach(cell => {
  if (ws[cell]) {
    ws[cell].s = {
      font: { bold: true, color: { rgb: "FF000000" } },
      alignment: { horizontal: "center", vertical: "center" },
      border: {
        bottom: { style: "thick", color: { rgb: "FF000000" } } // Nur unten dick!
      }
    };
  }
});

    // ===== Kategorien fett, in Spalte B =====
   // ===== Kategorien fett, in Spalte B (auch "Andere") =====
// ===== Kategorien fett, in Spalte B (auch "Andere") =====
// ===== Fix: Alle Kategorien bleiben in Spalte B, aber Border bei "Andere" wird entfernt =====
Object.keys(ws).forEach(cell => {
  const value = ws[cell]?.v;
  const allCategories = [...Object.values(categoryMap), "Andere"];
  if (typeof value === "string" && allCategories.includes(value)) {
    const cellRef = XLSX.utils.decode_cell(cell);

    // Kategorie bleibt in Spalte B (c = 1)
    if (cellRef.c !== 1) {
      const newCell = XLSX.utils.encode_cell({ r: cellRef.r, c: 1 });
      ws[newCell] = ws[cell];
      delete ws[cell];
    }

    // Wenn Kategorie = "Andere" → Border dieser Zeile löschen
    if (value === "Andere") {
      const row = cellRef.r;
      for (let c = 0; c <= 5; c++) {
        const addr = XLSX.utils.encode_cell({ r: row, c });
        if (ws[addr]?.s?.border) {
          ws[addr].s.border = {}; // entfernt Border in der gleichen Zeile
        }
      }
    }
  }
});

  
  
  
  
    // ===== Spaltenbreiten =====
    ws['!cols'] = [
      { width: 8 },
      { width: 25 },
      { width: 30 },
      { width: 22 },
      { width: 25 },
      { width: 15 }
    ];
  
    // ===== Dicker Außenrahmen =====
    const range = XLSX.utils.decode_range(ws['!ref']);
    const startRow = 0;
    const endRow = range.e.r;
    const startCol = range.s.c;
    const endCol = range.e.c;
  
    for (let r = startRow; r <= endRow; r++) {
      for (let c = startCol; c <= endCol; c++) {
        const addr = XLSX.utils.encode_cell({ r, c });
        if (!ws[addr]) ws[addr] = { t: "s", v: "" };
        ws[addr].s = ws[addr].s || {};
        ws[addr].s.border = ws[addr].s.border || {};
      }
    }
    // ===== Korrektur: Entferne Border in der Leerzeile nach "Andere" =====
// ==== Entfernt Border bei Kategorien ====
Object.keys(ws).forEach(cell => {
    const value = ws[cell]?.v;
    if (typeof value === "string" && Object.values(categoryMap).includes(value)) {
      for (let c = 0; c <= 5; c++) { // Spalten A–F
        const addr = XLSX.utils.encode_cell({ r: XLSX.utils.decode_cell(cell).r, c });
        if (ws[addr] && ws[addr].s && ws[addr].s.border) {
          ws[addr].s.border = {}; // Entfernt alle Linien für diese Zeile
        }
      }
    }
  });
  
  
    for (let c = startCol; c <= endCol; c++) {
      ws[XLSX.utils.encode_cell({ r: startRow, c })].s.border.top = { style: "thick", color: { rgb: "FF000000" } };
      ws[XLSX.utils.encode_cell({ r: endRow, c })].s.border.bottom = { style: "thick", color: { rgb: "FF000000" } };
    }
    for (let r = startRow; r <= endRow; r++) {
      ws[XLSX.utils.encode_cell({ r, c: startCol })].s.border.left = { style: "thick", color: { rgb: "FF000000" } };
      ws[XLSX.utils.encode_cell({ r, c: endCol })].s.border.right = { style: "thick", color: { rgb: "FF000000" } };
    }
  // ===== Zeilenumbruch aktivieren in Spalte Name =====
Object.keys(ws).forEach(cell => {
    if (cell.startsWith("B")) { // Spalte Name = B
      ws[cell].s = ws[cell].s || {};
      ws[cell].s.alignment = { wrapText: true, vertical: "center" };
    }
  });
  
  // ===== Speichern =====
  XLSX.utils.book_append_sheet(wb, ws, "BOM");
  XLSX.writeFile(wb, `MCR020_BOM_${new Date().toISOString().slice(0,10)}.xlsx`);
  }
