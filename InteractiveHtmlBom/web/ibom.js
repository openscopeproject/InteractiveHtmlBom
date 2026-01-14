// ibom.js

/* DOM manipulation and misc code */

var bomsplit;
var canvassplit;
var initDone = false;
var bomSortFunction = null;
var currentSortColumn = null;
var currentSortOrder = null;
var currentHighlightedRowId;
var highlightHandlers = [];
var footprintIndexToHandler = {};
var netsToHandler = {};
var markedFootprints = new Set();
var highlightedFootprints = [];
var highlightedNet = null;
var lastClicked;
var footprintColors = {};

function dbg(html) {
  dbgdiv.innerHTML = html;
}

function redrawIfInitDone() {
  if (initDone) {
    redrawCanvas(allcanvas.front);
    redrawCanvas(allcanvas.back);
  }
}

function padsVisible(value) {
  writeStorage("padsVisible", value);
  settings.renderPads = value;
  redrawIfInitDone();
}

function referencesVisible(value) {
  writeStorage("referencesVisible", value);
  settings.renderReferences = value;
  redrawIfInitDone();
}

function valuesVisible(value) {
  writeStorage("valuesVisible", value);
  settings.renderValues = value;
  redrawIfInitDone();
}

function tracksVisible(value) {
  writeStorage("tracksVisible", value);
  settings.renderTracks = value;
  redrawIfInitDone();
}

function zonesVisible(value) {
  writeStorage("zonesVisible", value);
  settings.renderZones = value;
  redrawIfInitDone();
}

function dnpOutline(value) {
  writeStorage("dnpOutline", value);
  settings.renderDnpOutline = value;
  redrawIfInitDone();
}

function setDarkMode(value) {
  if (value) {
    topmostdiv.classList.add("dark");
  } else {
    topmostdiv.classList.remove("dark");
  }
  writeStorage("darkmode", value);
  settings.darkMode = value;
  redrawIfInitDone();
  if (initDone) {
    populateBomTable();
  }
}

function setShowBOMColumn(field, value) {
  if (field === "references") {
    var rl = document.getElementById("reflookup");
    rl.disabled = !value;
    if (!value) {
      rl.value = "";
      updateRefLookup("");
    }
  }

  var n = settings.hiddenColumns.indexOf(field);
  if (value) {
    if (n != -1) {
      settings.hiddenColumns.splice(n, 1);
    }
  } else {
    if (n == -1) {
      settings.hiddenColumns.push(field);
    }
  }

  writeStorage("hiddenColumns", JSON.stringify(settings.hiddenColumns));

  if (initDone) {
    populateBomTable();
  }

  redrawIfInitDone();
}


function setFullscreen(value) {
  if (value) {
    document.documentElement.requestFullscreen();
  } else {
    document.exitFullscreen();
  }
}

function fabricationVisible(value) {
  writeStorage("fabricationVisible", value);
  settings.renderFabrication = value;
  redrawIfInitDone();
}

function silkscreenVisible(value) {
  writeStorage("silkscreenVisible", value);
  settings.renderSilkscreen = value;
  redrawIfInitDone();
}

function setHighlightPin1(value) {
  writeStorage("highlightpin1", value);
  settings.highlightpin1 = value;
  redrawIfInitDone();
}

function setHighlightRowOnClick(value) {
  settings.highlightRowOnClick = value;
  writeStorage("highlightRowOnClick", value);
  if (initDone) {
    populateBomTable();
  }
}

function setRainbowMode(value) {
  settings.rainbowMode = value;
  writeStorage("rainbowMode", value);
  var highlightAllLabel = document.getElementById("highlightAllLabel");
  if (highlightAllLabel) {
    highlightAllLabel.style.display = value ? "" : "none";
  }
  var showUnitsLabel = document.getElementById("showUnitsLabel");
  if (showUnitsLabel) {
    showUnitsLabel.style.display = value ? "" : "none";
  }
  populateBomTable();
  redrawIfInitDone();
}

function setHighlightAll(value) {
  settings.highlightAll = value;
  writeStorage("highlightAll", value);
  redrawIfInitDone();
}

function setShowUnits(value) {
  settings.showUnits = value;
  writeStorage("showUnits", value);
  redrawIfInitDone();
}

function getRainbowColor(index, total) {
  // 16 colors per round
  var hue = (index * (360 / 16)) % 360;
  var round = Math.floor(index / 16);
  var saturation = 100;
  var lightness = 50;
  var alpha = 0.7;

  if (round % 2 == 1) {
    saturation = 60;
    lightness = 60;
    alpha = 0.5;
  }

  return `hsla(${hue}, ${saturation}%, ${lightness}%, ${alpha})`;
}

function invertColor(hex) {
  if (hex.indexOf('#') === 0) {
    hex = hex.slice(1);
  }
  // convert 3-digit hex to 6-digits.
  if (hex.length === 3) {
    hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
  }
  if (hex.length !== 6) {
    return '#000000';
  }
  var r = (255 - parseInt(hex.slice(0, 2), 16)).toString(16),
    g = (255 - parseInt(hex.slice(2, 4), 16)).toString(16),
    b = (255 - parseInt(hex.slice(4, 6), 16)).toString(16);
  // pad each with zeros
  function padZero(str, len) {
    len = len || 2;
    var zeros = new Array(len).join('0');
    return (zeros + str).slice(-len);
  }
  return "#" + padZero(r) + padZero(g) + padZero(b);
}

function getValueColors(val) {
  var numMatch = val.match(/^([0-9.]+)/);
  if (!numMatch) return null;
  var s = numMatch[1];

  // Normalize leading decimal
  if (s.startsWith('.')) s = "0" + s;

  // Format to 3 digits + decimal
  if (s.indexOf('.') !== -1) {
    var parts = s.split('.');
    var intPart = parts[0];
    var fracPart = parts[1];
    var currentDigits = intPart.length + fracPart.length;
    if (currentDigits < 3) {
      fracPart += "0".repeat(3 - currentDigits);
    } else if (currentDigits > 3) {
      if (intPart.length >= 3) {
        intPart = intPart.substring(0, 3);
        fracPart = "";
      } else {
        fracPart = fracPart.substring(0, 3 - intPart.length);
      }
    }
    s = intPart + "." + fracPart;
  } else {
    if (s.length >= 3) {
      s = s.substring(0, 3) + ".";
    } else {
      s = s + ".";
      while (s.replace('.', '').length < 3) {
        s += "0";
      }
    }
  }

  var colors = [];
  var map = {
    '0': '#FFFFFF',
    '1': '#996633',
    '.': '#000000',
    '2': '#FF0000',
    '3': '#FF9900',
    '4': '#FFFF00',
    '5': '#00FF00',
    '6': '#0000FF',
    '7': '#FF00FF',
    '8': '#CCCCCC',
    '9': '#4B0082'
  };
  for (var i = 0; i < s.length; i++) {
    if (map[s[i]]) colors.push(map[s[i]]);
    else return null;
  }
  return colors.length === 4 ? colors : null;
}

function getUnitData(val, refPrefix) {
  // Match number, optional space, optional prefix, optional unit
  var match = val.match(/^([0-9.]+)\s*([pnumkMGµu]?)(F|Ω|H|V|A|R|Ohms|Ohm)?/i);
  if (!match) return null;
  var prefix = match[2];
  var unit = match[3];

  // Normalize prefix
  if (prefix === 'u') prefix = 'µ';

  // Infer unit from reference designator if missing
  if (!unit) {
    if (refPrefix.startsWith('C')) unit = 'F';
    else if (refPrefix.startsWith('R')) unit = 'Ω';
  } else {
    // Normalize unit
    if (unit.toUpperCase().startsWith('OHM') || unit.toUpperCase() === 'R') unit = 'Ω';
  }

  if (!unit) return null;

  var prefixColor = '#000000';
  var unitColor = '#000000';

  // Unit Colors
  if (unit === 'Ω') unitColor = '#707070'; // Dark Silver
  else if (unit === 'F') unitColor = '#8C7853'; // Dark Brass
  
  // Prefix Colors
  // 2: Red, 3: Orange, 6: Blue, 9: Indigo
  var colorMap = {
      '2': '#FF0000', // Red
      '3': '#FF9900', // Orange
      '6': '#0000FF', // Blue
      '9': '#4B0082'  // Indigo
  };

  if (prefix === 'k') prefixColor = colorMap['3'];
  else if (prefix === 'M') prefixColor = colorMap['6'];
  else if (prefix === 'G') prefixColor = colorMap['9'];
  else if (prefix === 'm') prefixColor = invertColor(colorMap['3']);
  else if (prefix === 'µ') prefixColor = invertColor(colorMap['6']);
  else if (prefix === 'n') prefixColor = invertColor(colorMap['9']);
  else if (prefix === 'p') prefixColor = invertColor(colorMap['2']);

  return {
    text: (prefix || "") + unit,
    prefixColor: prefixColor,
    unitColor: unitColor
  };
}

function getStoredCheckboxRefs(checkbox) {
  function convert(ref) {
    var intref = parseInt(ref);
    if (isNaN(intref)) {
      for (var i = 0; i < pcbdata.footprints.length; i++) {
        if (pcbdata.footprints[i].ref == ref) {
          return i;
        }
      }
      return -1;
    } else {
      return intref;
    }
  }
  if (!(checkbox in settings.checkboxStoredRefs)) {
    var val = readStorage("checkbox_" + checkbox);
    settings.checkboxStoredRefs[checkbox] = val ? val : "";
  }
  if (!settings.checkboxStoredRefs[checkbox]) {
    return new Set();
  } else {
    return new Set(settings.checkboxStoredRefs[checkbox].split(",").map(r => convert(r)).filter(a => a >= 0));
  }
}

function getCheckboxState(checkbox, references) {
  var storedRefsSet = getStoredCheckboxRefs(checkbox);
  var currentRefsSet = new Set(references.map(r => r[1]));
  // Get difference of current - stored
  var difference = new Set(currentRefsSet);
  for (ref of storedRefsSet) {
    difference.delete(ref);
  }
  if (difference.size == 0) {
    // All the current refs are stored
    return "checked";
  } else if (difference.size == currentRefsSet.size) {
    // None of the current refs are stored
    return "unchecked";
  } else {
    // Some of the refs are stored
    return "indeterminate";
  }
}

function setBomCheckboxState(checkbox, element, references) {
  var state = getCheckboxState(checkbox, references);
  element.checked = (state == "checked");
  element.indeterminate = (state == "indeterminate");
}

function createCheckboxHandlers(input, checkbox, references, row) {
  var clickHandler = () => {
    refsSet = getStoredCheckboxRefs(checkbox);
    var markWhenChecked = settings.markWhenChecked == checkbox;
    eventArgs = {
      checkbox: checkbox,
      refs: references,
    }
    if (input.checked) {
      // checkbox ticked
      for (var ref of references) {
        refsSet.add(ref[1]);
      }
      if (markWhenChecked) {
        row.classList.add("checked");
        for (var ref of references) {
          markedFootprints.add(ref[1]);
        }
        drawHighlights();
      }
      eventArgs.state = 'checked';
    } else {
      // checkbox unticked
      for (var ref of references) {
        refsSet.delete(ref[1]);
      }
      if (markWhenChecked) {
        row.classList.remove("checked");
        for (var ref of references) {
          markedFootprints.delete(ref[1]);
        }
        drawHighlights();
      }
      eventArgs.state = 'unchecked';
    }
    settings.checkboxStoredRefs[checkbox] = [...refsSet].join(",");
    writeStorage("checkbox_" + checkbox, settings.checkboxStoredRefs[checkbox]);
    updateCheckboxStats(checkbox);
    EventHandler.emitEvent(IBOM_EVENT_TYPES.CHECKBOX_CHANGE_EVENT, eventArgs);
  }

  return [
    (e) => {
      clickHandler();
    },
    (e) => {
      e.preventDefault();
      if (row.onmousemove) row.onmousemove();
    },
    (e) => {
      e.preventDefault();
      input.checked = !input.checked;
      input.indeterminate = false;
      clickHandler();
    }
  ];
}

function clearHighlightedFootprints() {
  if (currentHighlightedRowId) {
    document.getElementById(currentHighlightedRowId).classList.remove("highlighted");
    currentHighlightedRowId = null;
    highlightedFootprints = [];
    highlightedNet = null;
  }
}

function createRowHighlightHandler(rowid, refs, net) {
  return function () {
    if (currentHighlightedRowId) {
      if (currentHighlightedRowId == rowid) {
        return;
      }
      document.getElementById(currentHighlightedRowId).classList.remove("highlighted");
    }
    document.getElementById(rowid).classList.add("highlighted");
    currentHighlightedRowId = rowid;
    highlightedFootprints = refs ? refs.map(r => r[1]) : [];
    highlightedNet = net;
    drawHighlights();
    EventHandler.emitEvent(
      IBOM_EVENT_TYPES.HIGHLIGHT_EVENT, {
      rowid: rowid,
      refs: refs,
      net: net
    });
  }
}

function updateNetColors() {
  writeStorage("netColors", JSON.stringify(settings.netColors));
  redrawIfInitDone();
}

function netColorChangeHandler(net) {
  return (event) => {
    settings.netColors[net] = event.target.value;
    updateNetColors();
  }
}

function netColorRightClick(net) {
  return (event) => {
    if (event.button == 2) {
      event.preventDefault();
      event.stopPropagation();

      var style = getComputedStyle(topmostdiv);
      var defaultNetColor = style.getPropertyValue('--track-color').trim();
      event.target.value = defaultNetColor;
      delete settings.netColors[net];
      updateNetColors();
    }
  }
}

function entryMatches(entry) {
  if (settings.bommode == "netlist") {
    // entry is just a net name
    return entry.toLowerCase().indexOf(filter) >= 0;
  }
  // check refs
  if (!settings.hiddenColumns.includes("References")) {
    for (var ref of entry) {
      if (ref[0].toLowerCase().indexOf(filter) >= 0) {
        return true;
      }
    }
  }
  // check fields
  for (var i in config.fields) {
    var f = config.fields[i];
    if (!settings.hiddenColumns.includes(f)) {
      for (var ref of entry) {
        if (String(pcbdata.bom.fields[ref[1]][i]).toLowerCase().indexOf(filter) >= 0) {
          return true;
        }
      }
    }
  }
  return false;
}

function findRefInEntry(entry) {
  return entry.filter(r => r[0].toLowerCase() == reflookup);
}

function highlightFilter(s) {
  if (!filter) {
    return s;
  }
  var parts = s.toLowerCase().split(filter);
  if (parts.length == 1) {
    return s;
  }
  var r = "";
  var pos = 0;
  for (var i in parts) {
    if (i > 0) {
      r += '<mark class="highlight">' +
        s.substring(pos, pos + filter.length) +
        '</mark>';
      pos += filter.length;
    }
    r += s.substring(pos, pos + parts[i].length);
    pos += parts[i].length;
  }
  return r;
}

function getBomListByLayer(layer) {
  switch (layer) {
    case 'F': return pcbdata.bom.F.slice();
    case 'B': return pcbdata.bom.B.slice();
    case 'FB': return pcbdata.bom.both.slice();
  }
  return [];
}

function getSelectedBomList() {
  if (settings.bommode == "netlist") {
    return pcbdata.nets.slice();
  }
  var out = getBomListByLayer(settings.canvaslayout);

  if (settings.bommode == "ungrouped") {
    // expand bom table
    var expandedTable = [];
    for (var bomentry of out) {
      for (var ref of bomentry) {
        expandedTable.push([ref]);
      }
    }
    return expandedTable;
  }

  return out;
}

function checkboxSetUnsetAllHandler(checkboxname) {
  return function () {
    var checkboxnum = 0;
    while (checkboxnum < settings.checkboxes.length &&
      settings.checkboxes[checkboxnum].toLowerCase() != checkboxname.toLowerCase()) {
      checkboxnum++;
    }
    if (checkboxnum >= settings.checkboxes.length) {
      return;
    }
    var allset = true;
    var checkbox;
    var row;
    for (row of bombody.childNodes) {
      checkbox = row.childNodes[checkboxnum + 1].childNodes[0];
      if (!checkbox.checked || checkbox.indeterminate) {
        allset = false;
        break;
      }
    }
    for (row of bombody.childNodes) {
      checkbox = row.childNodes[checkboxnum + 1].childNodes[0];
      checkbox.checked = !allset;
      checkbox.indeterminate = false;
      checkbox.onchange();
    }
  }
}

function createColumnHeader(name, cls, comparator, is_checkbox = false) {
  var th = document.createElement("TH");
  th.innerHTML = name;
  th.classList.add(cls);
  if (is_checkbox)
    th.setAttribute("col_name", "bom-checkbox");
  else
    th.setAttribute("col_name", name);
  var span = document.createElement("SPAN");
  span.classList.add("sortmark");
  span.classList.add("none");
  th.appendChild(span);
  var spacer = document.createElement("div");
  spacer.className = "column-spacer";
  th.appendChild(spacer);
  spacer.onclick = function () {
    if (currentSortColumn && th !== currentSortColumn) {
      // Currently sorted by another column
      currentSortColumn.childNodes[1].classList.remove(currentSortOrder);
      currentSortColumn.childNodes[1].classList.add("none");
      currentSortColumn = null;
      currentSortOrder = null;
    }
    if (currentSortColumn && th === currentSortColumn) {
      // Already sorted by this column
      if (currentSortOrder == "asc") {
        // Sort by this column, descending order
        bomSortFunction = function (a, b) {
          return -comparator(a, b);
        }
        currentSortColumn.childNodes[1].classList.remove("asc");
        currentSortColumn.childNodes[1].classList.add("desc");
        currentSortOrder = "desc";
      } else {
        // Unsort
        bomSortFunction = null;
        currentSortColumn.childNodes[1].classList.remove("desc");
        currentSortColumn.childNodes[1].classList.add("none");
        currentSortColumn = null;
        currentSortOrder = null;
      }
    } else {
      // Sort by this column, ascending order
      bomSortFunction = comparator;
      currentSortColumn = th;
      currentSortColumn.childNodes[1].classList.remove("none");
      currentSortColumn.childNodes[1].classList.add("asc");
      currentSortOrder = "asc";
    }
    populateBomBody();
  }
  if (is_checkbox) {
    spacer.onclick = fancyDblClickHandler(
      spacer, spacer.onclick, checkboxSetUnsetAllHandler(name));
  }
  return th;
}

function populateBomHeader(placeHolderColumn = null, placeHolderElements = null) {
  while (bomhead.firstChild) {
    bomhead.removeChild(bomhead.firstChild);
  }
  var tr = document.createElement("TR");
  var th = document.createElement("TH");
  th.classList.add("numCol");

  var vismenu = document.createElement("div");
  vismenu.id = "vismenu";
  vismenu.classList.add("menu");

  var visbutton = document.createElement("div");
  visbutton.classList.add("visbtn");
  visbutton.classList.add("hideonprint");

  var viscontent = document.createElement("div");
  viscontent.classList.add("menu-content");
  viscontent.id = "vismenu-content";

  settings.columnOrder.forEach(column => {
    if (typeof column !== "string")
      return;

    // Skip empty columns
    if (column === "checkboxes" && settings.checkboxes.length == 0)
      return;
    else if (column === "Quantity" && settings.bommode == "ungrouped")
      return;

    var label = document.createElement("label");
    label.classList.add("menu-label");

    var input = document.createElement("input");
    input.classList.add("visibility_checkbox");
    input.type = "checkbox";
    input.onchange = function (e) {
      setShowBOMColumn(column, e.target.checked)
    };
    input.checked = !(settings.hiddenColumns.includes(column));

    label.appendChild(input);
    if (column.length > 0)
      label.append(column[0].toUpperCase() + column.slice(1));

    viscontent.appendChild(label);
  });

  viscontent.childNodes[0].classList.add("menu-label-top");

  vismenu.appendChild(visbutton);
  if (settings.bommode != "netlist") {
    vismenu.appendChild(viscontent);
    th.appendChild(vismenu);
  }
  tr.appendChild(th);

  var checkboxCompareClosure = function (checkbox) {
    return (a, b) => {
      var stateA = getCheckboxState(checkbox, a);
      var stateB = getCheckboxState(checkbox, b);
      if (stateA > stateB) return -1;
      if (stateA < stateB) return 1;
      return 0;
    }
  }
  var stringFieldCompareClosure = function (fieldIndex) {
    return (a, b) => {
      var fa = pcbdata.bom.fields[a[0][1]][fieldIndex];
      var fb = pcbdata.bom.fields[b[0][1]][fieldIndex];
      if (fa != fb) return fa > fb ? 1 : -1;
      else return 0;
    }
  }
  var referenceRegex = /(?<prefix>[^0-9]+)(?<number>[0-9]+)/;
  var compareRefs = (a, b) => {
    var ra = referenceRegex.exec(a);
    var rb = referenceRegex.exec(b);
    if (ra === null || rb === null) {
      if (a != b) return a > b ? 1 : -1;
      return 0;
    } else {
      if (ra.groups.prefix != rb.groups.prefix) {
        return ra.groups.prefix > rb.groups.prefix ? 1 : -1;
      }
      if (ra.groups.number != rb.groups.number) {
        return parseInt(ra.groups.number) > parseInt(rb.groups.number) ? 1 : -1;
      }
      return 0;
    }
  }
  if (settings.bommode == "netlist") {
    tr.appendChild(createColumnHeader("Net name", "bom-netname", (a, b) => {
      if (a > b) return -1;
      if (a < b) return 1;
      return 0;
    }));
    tr.appendChild(createColumnHeader("Color", "bom-color", (a, b) => {
      return 0;
    }));
  } else {
    // Filter hidden columns
    var columns = settings.columnOrder.filter(e => !settings.hiddenColumns.includes(e));
    var valueIndex = config.fields.indexOf("Value");
    var footprintIndex = config.fields.indexOf("Footprint");
    columns.forEach((column) => {
      if (column === placeHolderColumn) {
        var n = 1;
        if (column === "checkboxes")
          n = settings.checkboxes.length;
        for (i = 0; i < n; i++) {
          td = placeHolderElements.shift();
          tr.appendChild(td);
        }
        return;
      } else if (column === "checkboxes") {
        for (var checkbox of settings.checkboxes) {
          th = createColumnHeader(
            checkbox, "bom-checkbox", checkboxCompareClosure(checkbox), true);
          tr.appendChild(th);
        }
      } else if (column === "References") {
        tr.appendChild(createColumnHeader("References", "references", (a, b) => {
          var i = 0;
          while (i < a.length && i < b.length) {
            if (a[i][0] != b[i][0]) return compareRefs(a[i][0], b[i][0]);
            i++;
          }
          return a.length - b.length;
        }));
      } else if (column === "Value") {
        tr.appendChild(createColumnHeader("Value", "value", (a, b) => {
          var ra = a[0][1], rb = b[0][1];
          return valueCompare(
            pcbdata.bom.parsedValues[ra], pcbdata.bom.parsedValues[rb],
            pcbdata.bom.fields[ra][valueIndex], pcbdata.bom.fields[rb][valueIndex]);
        }));
        return;
      } else if (column === "Footprint") {
        tr.appendChild(createColumnHeader(
          "Footprint", "footprint", stringFieldCompareClosure(footprintIndex)));
      } else if (column === "Quantity" && settings.bommode == "grouped") {
        tr.appendChild(createColumnHeader("Quantity", "quantity", (a, b) => {
          return a.length - b.length;
        }));
      } else {
        // Other fields
        var i = config.fields.indexOf(column);
        if (i < 0)
          return;
        tr.appendChild(createColumnHeader(
          column, `field${i + 1}`, stringFieldCompareClosure(i)));
      }
    });
  }
  bomhead.appendChild(tr);
}

function populateBomBody(placeholderColumn = null, placeHolderElements = null) {
  const urlRegex = /^(https?:\/\/[^\s\/$.?#][^\s]*|file:\/\/([a-zA-Z]:|\/)[^\x00]+)$/;
  while (bom.firstChild) {
    bom.removeChild(bom.firstChild);
  }
  highlightHandlers = [];
  footprintIndexToHandler = {};
  netsToHandler = {};
  currentHighlightedRowId = null;
  footprintColors = {};
  var first = true;
  var style = getComputedStyle(topmostdiv);
  var defaultNetColor = style.getPropertyValue('--track-color').trim();

  bomtable = getSelectedBomList();

  if (bomSortFunction) {
    bomtable = bomtable.sort(bomSortFunction);
  }
  for (var i in bomtable) {
    var bomentry = bomtable[i];
    if (filter && !entryMatches(bomentry)) {
      continue;
    }
    var references = null;
    var netname = null;
    var tr = document.createElement("TR");
    var td = document.createElement("TD");
    var rownum = +i + 1;
    tr.id = "bomrow" + rownum;
    td.textContent = rownum;
    tr.appendChild(td);
    if (settings.bommode == "netlist") {
      netname = bomentry;
      td = document.createElement("TD");
      td.innerHTML = highlightFilter(netname ? netname : "&lt;no net&gt;");
      tr.appendChild(td);
      var color = settings.netColors[netname] || defaultNetColor;
      td = document.createElement("TD");
      var colorBox = document.createElement("INPUT");
      colorBox.type = "color";
      colorBox.value = color;
      colorBox.onchange = netColorChangeHandler(netname);
      colorBox.onmouseup = netColorRightClick(netname);
      colorBox.oncontextmenu = (e) => e.preventDefault();
      td.appendChild(colorBox);
      td.classList.add("color-column");
      tr.appendChild(td);
    } else {
      if (reflookup) {
        references = findRefInEntry(bomentry);
        if (references.length == 0) {
          continue;
        }
      } else {
        references = bomentry;
      }
      // Filter hidden columns
      var columns = settings.columnOrder.filter(e => !settings.hiddenColumns.includes(e));
      columns.forEach((column) => {
        if (column === placeholderColumn) {
          var n = 1;
          if (column === "checkboxes")
            n = settings.checkboxes.length;
          for (i = 0; i < n; i++) {
            td = placeHolderElements.shift();
            tr.appendChild(td);
          }
          return;
        } else if (column === "checkboxes") {
          for (var checkbox of settings.checkboxes) {
            if (checkbox) {
              td = document.createElement("TD");
              var input = document.createElement("input");
              input.type = "checkbox";
              [input.onchange, td.ontouchstart, td.ontouchend] = createCheckboxHandlers(input, checkbox, references, tr);
              setBomCheckboxState(checkbox, input, references);
              if (input.checked && settings.markWhenChecked == checkbox) {
                tr.classList.add("checked");
              }
              td.appendChild(input);
              tr.appendChild(td);
            }
          }
        } else if (column === "References") {
          td = document.createElement("TD");
          td.innerHTML = highlightFilter(references.map(r => r[0]).join(", "));
          tr.appendChild(td);
        } else if (column === "Quantity" && settings.bommode == "grouped") {
          // Quantity
          td = document.createElement("TD");
          td.textContent = references.length;
          tr.appendChild(td);
        } else {
          // All the other fields
          var field_index = config.fields.indexOf(column)
          if (field_index < 0)
            return;
          var valueSet = new Set();
          references.map(r => r[1]).forEach((id) => valueSet.add(pcbdata.bom.fields[id][field_index]));
          td = document.createElement("TD");
          var output = new Array();
          for (let item of valueSet) {
            const visible = highlightFilter(String(item));
            if (typeof item === 'string' && item.match(urlRegex)) {
              output.push(`<a href="${item}" target="_blank">${visible}</a>`);
            } else {
              output.push(visible);
            }
          }
          td.innerHTML = output.join(", ");

          // Add color bands if rainbow mode is enabled and this is the Value column
          if (settings.rainbowMode && column === "Value" && references) {
            var firstRef = references[0][0];
            if (firstRef.startsWith('C') || firstRef.startsWith('R')) {
              var val = pcbdata.bom.fields[bomentry[0][1]][field_index];
              var colors = getValueColors(val);
              if (colors) {
                var bandContainer = document.createElement("div");
                bandContainer.style.display = "flex";
                bandContainer.style.height = "5px";
                bandContainer.style.marginTop = "2px";
                bandContainer.style.width = "100%";
                for (var c of colors) {
                  var band = document.createElement("div");
                  band.style.flex = "1";
                  band.style.backgroundColor = c;
                  bandContainer.appendChild(band);
                }
                td.appendChild(bandContainer);
              }
            }
          }

          tr.appendChild(td);
        }
      });

      if (settings.rainbowMode && references) {
        var firstRef = references[0][0];
        if (firstRef.startsWith('C') || firstRef.startsWith('R')) {
          var valueIndex = config.fields.indexOf("Value");
          var val = pcbdata.bom.fields[bomentry[0][1]][valueIndex];
          var colors = getValueColors(val);
          var unitData = getUnitData(val, firstRef);
          if (colors) {
            for (var ref of references) {
              footprintColors[ref[1]] = {
                bands: colors,
                unit: unitData
              };
            }
          }
        }
      }
    }
    bom.appendChild(tr);
    var handler = createRowHighlightHandler(tr.id, references, netname);
    if (settings.highlightRowOnClick) {
      tr.onmousedown = handler;
    } else {
      tr.onmousemove = handler;
    }
    highlightHandlers.push({
      id: tr.id,
      handler: handler,
    });
    if (references !== null) {
      for (var refIndex of references.map(r => r[1])) {
        footprintIndexToHandler[refIndex] = handler;
      }
    }
    if (netname !== null) {
      netsToHandler[netname] = handler;
    }
    if ((filter || reflookup) && first) {
      handler();
      first = false;
    }
  }
  EventHandler.emitEvent(
    IBOM_EVENT_TYPES.BOM_BODY_CHANGE_EVENT, {
    filter: filter,
    reflookup: reflookup,
    checkboxes: settings.checkboxes,
    bommode: settings.bommode,
  });
}

function highlightPreviousRow() {
  if (!currentHighlightedRowId) {
    highlightHandlers[highlightHandlers.length - 1].handler();
  } else {
    if (highlightHandlers.length > 1 &&
      highlightHandlers[0].id == currentHighlightedRowId) {
      highlightHandlers[highlightHandlers.length - 1].handler();
    } else {
      for (var i = 0; i < highlightHandlers.length - 1; i++) {
        if (highlightHandlers[i + 1].id == currentHighlightedRowId) {
          highlightHandlers[i].handler();
          break;
        }
      }
    }
  }
  smoothScrollToRow(currentHighlightedRowId);
}

function highlightNextRow() {
  if (!currentHighlightedRowId) {
    highlightHandlers[0].handler();
  } else {
    if (highlightHandlers.length > 1 &&
      highlightHandlers[highlightHandlers.length - 1].id == currentHighlightedRowId) {
      highlightHandlers[0].handler();
    } else {
      for (var i = 1; i < highlightHandlers.length; i++) {
        if (highlightHandlers[i - 1].id == currentHighlightedRowId) {
          highlightHandlers[i].handler();
          break;
        }
      }
    }
  }
  smoothScrollToRow(currentHighlightedRowId);
}

function populateBomTable() {
  populateBomHeader();
  populateBomBody();
  setBomHandlers();
  resizableGrid(bomhead);
}

function footprintsClicked(footprintIndexes) {
  var lastClickedIndex = footprintIndexes.indexOf(lastClicked);
  for (var i = 1; i <= footprintIndexes.length; i++) {
    var refIndex = footprintIndexes[(lastClickedIndex + i) % footprintIndexes.length];
    if (refIndex in footprintIndexToHandler) {
      lastClicked = refIndex;
      footprintIndexToHandler[refIndex]();
      smoothScrollToRow(currentHighlightedRowId);
      break;
    }
  }
}

function netClicked(net) {
  if (net in netsToHandler) {
    netsToHandler[net]();
    smoothScrollToRow(currentHighlightedRowId);
  } else {
    clearHighlightedFootprints();
    highlightedNet = net;
    drawHighlights();
  }
}

function updateFilter(input) {
  filter = input.toLowerCase();
  populateBomTable();
}

function updateRefLookup(input) {
  reflookup = input.toLowerCase();
  populateBomTable();
}

function changeCanvasLayout(layout) {
  document.getElementById("fl-btn").classList.remove("depressed");
  document.getElementById("fb-btn").classList.remove("depressed");
  document.getElementById("bl-btn").classList.remove("depressed");
  switch (layout) {
    case 'F':
      document.getElementById("fl-btn").classList.add("depressed");
      if (settings.bomlayout != "bom-only") {
        canvassplit.collapse(1);
      }
      break;
    case 'B':
      document.getElementById("bl-btn").classList.add("depressed");
      if (settings.bomlayout != "bom-only") {
        canvassplit.collapse(0);
      }
      break;
    default:
      document.getElementById("fb-btn").classList.add("depressed");
      if (settings.bomlayout != "bom-only") {
        canvassplit.setSizes([50, 50]);
      }
  }
  settings.canvaslayout = layout;
  writeStorage("canvaslayout", layout);
  resizeAll();
  changeBomMode(settings.bommode);
}

function populateMetadata() {
  document.getElementById("title").innerHTML = pcbdata.metadata.title;
  document.getElementById("revision").innerHTML = "Rev: " + pcbdata.metadata.revision;
  document.getElementById("company").innerHTML = pcbdata.metadata.company;
  document.getElementById("filedate").innerHTML = pcbdata.metadata.date;
  if (pcbdata.metadata.title != "") {
    document.title = pcbdata.metadata.title + " BOM";
  }
  // Calculate board stats
  var fp_f = 0,
    fp_b = 0,
    pads_f = 0,
    pads_b = 0,
    pads_th = 0;
  for (var i = 0; i < pcbdata.footprints.length; i++) {
    if (pcbdata.bom.skipped.includes(i)) continue;
    var mod = pcbdata.footprints[i];
    if (mod.layer == "F") {
      fp_f++;
    } else {
      fp_b++;
    }
    for (var pad of mod.pads) {
      if (pad.type == "th") {
        pads_th++;
      } else {
        if (pad.layers.includes("F")) {
          pads_f++;
        }
        if (pad.layers.includes("B")) {
          pads_b++;
        }
      }
    }
  }
  document.getElementById("stats-components-front").innerHTML = fp_f;
  document.getElementById("stats-components-back").innerHTML = fp_b;
  document.getElementById("stats-components-total").innerHTML = fp_f + fp_b;
  document.getElementById("stats-groups-front").innerHTML = pcbdata.bom.F.length;
  document.getElementById("stats-groups-back").innerHTML = pcbdata.bom.B.length;
  document.getElementById("stats-groups-total").innerHTML = pcbdata.bom.both.length;
  document.getElementById("stats-smd-pads-front").innerHTML = pads_f;
  document.getElementById("stats-smd-pads-back").innerHTML = pads_b;
  document.getElementById("stats-smd-pads-total").innerHTML = pads_f + pads_b;
  document.getElementById("stats-th-pads").innerHTML = pads_th;
  // Update version string
  document.getElementById("github-link").innerHTML = "InteractiveHtmlBom&nbsp;" +
    /^v\d+\.\d+/.exec(pcbdata.ibom_version)[0];
}

function changeBomLayout(layout) {
  document.getElementById("bom-btn").classList.remove("depressed");
  document.getElementById("lr-btn").classList.remove("depressed");
  document.getElementById("tb-btn").classList.remove("depressed");
  switch (layout) {
    case 'bom-only':
      document.getElementById("bom-btn").classList.add("depressed");
      if (bomsplit) {
        bomsplit.destroy();
        bomsplit = null;
        canvassplit.destroy();
        canvassplit = null;
      }
      document.getElementById("frontcanvas").style.display = "none";
      document.getElementById("backcanvas").style.display = "none";
      document.getElementById("topmostdiv").style.height = "";
      document.getElementById("topmostdiv").style.display = "block";
      break;
    case 'top-bottom':
      document.getElementById("tb-btn").classList.add("depressed");
      document.getElementById("frontcanvas").style.display = "";
      document.getElementById("backcanvas").style.display = "";
      document.getElementById("topmostdiv").style.height = "100%";
      document.getElementById("topmostdiv").style.display = "flex";
      document.getElementById("bomdiv").classList.remove("split-horizontal");
      document.getElementById("canvasdiv").classList.remove("split-horizontal");
      document.getElementById("frontcanvas").classList.add("split-horizontal");
      document.getElementById("backcanvas").classList.add("split-horizontal");
      if (bomsplit) {
        bomsplit.destroy();
        bomsplit = null;
        canvassplit.destroy();
        canvassplit = null;
      }
      bomsplit = Split(['#bomdiv', '#canvasdiv'], {
        sizes: [50, 50],
        onDragEnd: resizeAll,
        direction: "vertical",
        gutterSize: 5
      });
      canvassplit = Split(['#frontcanvas', '#backcanvas'], {
        sizes: [50, 50],
        gutterSize: 5,
        onDragEnd: resizeAll
      });
      break;
    case 'left-right':
      document.getElementById("lr-btn").classList.add("depressed");
      document.getElementById("frontcanvas").style.display = "";
      document.getElementById("backcanvas").style.display = "";
      document.getElementById("topmostdiv").style.height = "100%";
      document.getElementById("topmostdiv").style.display = "flex";
      document.getElementById("bomdiv").classList.add("split-horizontal");
      document.getElementById("canvasdiv").classList.add("split-horizontal");
      document.getElementById("frontcanvas").classList.remove("split-horizontal");
      document.getElementById("backcanvas").classList.remove("split-horizontal");
      if (bomsplit) {
        bomsplit.destroy();
        bomsplit = null;
        canvassplit.destroy();
        canvassplit = null;
      }
      bomsplit = Split(['#bomdiv', '#canvasdiv'], {
        sizes: [50, 50],
        onDragEnd: resizeAll,
        gutterSize: 5
      });
      canvassplit = Split(['#frontcanvas', '#backcanvas'], {
        sizes: [50, 50],
        gutterSize: 5,
        direction: "vertical",
        onDragEnd: resizeAll
      });
  }
  settings.bomlayout = layout;
  writeStorage("bomlayout", layout);
  changeCanvasLayout(settings.canvaslayout);
}

function changeBomMode(mode) {
  document.getElementById("bom-grouped-btn").classList.remove("depressed");
  document.getElementById("bom-ungrouped-btn").classList.remove("depressed");
  document.getElementById("bom-netlist-btn").classList.remove("depressed");
  var chkbxs = document.getElementsByClassName("visibility_checkbox");

  switch (mode) {
    case 'grouped':
      document.getElementById("bom-grouped-btn").classList.add("depressed");
      for (var i = 0; i < chkbxs.length; i++) {
        chkbxs[i].disabled = false;
      }
      break;
    case 'ungrouped':
      document.getElementById("bom-ungrouped-btn").classList.add("depressed");
      for (var i = 0; i < chkbxs.length; i++) {
        chkbxs[i].disabled = false;
      }
      break;
    case 'netlist':
      document.getElementById("bom-netlist-btn").classList.add("depressed");
      for (var i = 0; i < chkbxs.length; i++) {
        chkbxs[i].disabled = true;
      }
  }

  writeStorage("bommode", mode);
  if (mode != settings.bommode) {
    settings.bommode = mode;
    bomSortFunction = null;
    currentSortColumn = null;
    currentSortOrder = null;
    clearHighlightedFootprints();
  }
  populateBomTable();
}

function focusFilterField() {
  focusInputField(document.getElementById("filter"));
}

function focusRefLookupField() {
  focusInputField(document.getElementById("reflookup"));
}

function toggleBomCheckbox(bomrowid, checkboxnum) {
  if (!bomrowid || checkboxnum > settings.checkboxes.length) {
    return;
  }
  var bomrow = document.getElementById(bomrowid);
  var childNum = checkboxnum + settings.columnOrder.indexOf("checkboxes");
  var checkbox = bomrow.childNodes[childNum].childNodes[0];
  checkbox.checked = !checkbox.checked;
  checkbox.indeterminate = false;
  checkbox.onchange();
}

function checkBomCheckbox(bomrowid, checkboxname) {
  var checkboxnum = 0;
  while (checkboxnum < settings.checkboxes.length &&
    settings.checkboxes[checkboxnum].toLowerCase() != checkboxname.toLowerCase()) {
    checkboxnum++;
  }
  if (!bomrowid || checkboxnum >= settings.checkboxes.length) {
    return;
  }
  var bomrow = document.getElementById(bomrowid);
  var childNum = checkboxnum + 1 + settings.columnOrder.indexOf("checkboxes");
  var checkbox = bomrow.childNodes[childNum].childNodes[0];
  checkbox.checked = true;
  checkbox.indeterminate = false;
  checkbox.onchange();
}

function setBomCheckboxes(value) {
  writeStorage("bomCheckboxes", value);
  settings.checkboxes = value.split(",").map((e) => e.trim()).filter((e) => e);
  prepCheckboxes();
  populateMarkWhenCheckedOptions();
  setMarkWhenChecked(settings.markWhenChecked);
}

function setMarkWhenChecked(value) {
  writeStorage("markWhenChecked", value);
  settings.markWhenChecked = value;
  markedFootprints.clear();
  for (var ref of (value ? getStoredCheckboxRefs(value) : [])) {
    markedFootprints.add(ref);
  }
  populateBomTable();
  drawHighlights();
}

function prepCheckboxes() {
  var table = document.getElementById("checkbox-stats");
  while (table.childElementCount > 1) {
    table.removeChild(table.lastChild);
  }
  if (settings.checkboxes.length) {
    table.style.display = "";
  } else {
    table.style.display = "none";
  }
  for (var checkbox of settings.checkboxes) {
    var tr = document.createElement("TR");
    var td = document.createElement("TD");
    td.innerHTML = checkbox;
    tr.appendChild(td);
    td = document.createElement("TD");
    td.id = "checkbox-stats-" + checkbox;
    var progressbar = document.createElement("div");
    progressbar.classList.add("bar");
    td.appendChild(progressbar);
    var text = document.createElement("div");
    text.classList.add("text");
    td.appendChild(text);
    tr.appendChild(td);
    table.appendChild(tr);
    updateCheckboxStats(checkbox);
  }
}

function populateMarkWhenCheckedOptions() {
  var container = document.getElementById("markWhenCheckedContainer");

  if (settings.checkboxes.length == 0) {
    container.parentElement.style.display = "none";
    return;
  }

  container.innerHTML = '';
  container.parentElement.style.display = "inline-block";

  function createOption(name, displayName) {
    var id = "markWhenChecked-" + name;

    var div = document.createElement("div");
    div.classList.add("radio-container");

    var input = document.createElement("input");
    input.type = "radio";
    input.name = "markWhenChecked";
    input.value = name;
    input.id = id;
    input.onchange = () => setMarkWhenChecked(name);
    div.appendChild(input);

    // Preserve the selected element when the checkboxes change
    if (name == settings.markWhenChecked) {
      input.checked = true;
    }

    var label = document.createElement("label");
    label.innerHTML = displayName;
    label.htmlFor = id;
    div.appendChild(label);

    container.appendChild(div);
  }
  createOption("", "None");
  for (var checkbox of settings.checkboxes) {
    createOption(checkbox, checkbox);
  }
}

function updateCheckboxStats(checkbox) {
  var checked = getStoredCheckboxRefs(checkbox).size;
  var total = pcbdata.footprints.length - pcbdata.bom.skipped.length;
  var percent = checked * 100.0 / total;
  var td = document.getElementById("checkbox-stats-" + checkbox);
  td.firstChild.style.width = percent + "%";
  td.lastChild.innerHTML = checked + "/" + total + " (" + Math.round(percent) + "%)";
}

function constrain(number, min, max) {
  return Math.min(Math.max(parseInt(number), min), max);
}

document.onkeydown = function (e) {
  switch (e.key) {
    case "n":
      if (document.activeElement.type == "text") {
        return;
      }
      if (currentHighlightedRowId !== null) {
        checkBomCheckbox(currentHighlightedRowId, "placed");
        highlightNextRow();
        e.preventDefault();
      }
      break;
    case "ArrowUp":
      highlightPreviousRow();
      e.preventDefault();
      break;
    case "ArrowDown":
      highlightNextRow();
      e.preventDefault();
      break;
    case "ArrowLeft":
    case "ArrowRight":
      if (document.activeElement.type != "text") {
        e.preventDefault();
        let boardRotationElement = document.getElementById("boardRotation")
        settings.boardRotation = parseInt(boardRotationElement.value);  // degrees / 5
        if (e.key == "ArrowLeft") {
          settings.boardRotation += 3;  // 15 degrees
        }
        else {
          settings.boardRotation -= 3;
        }
        settings.boardRotation = constrain(settings.boardRotation, boardRotationElement.min, boardRotationElement.max);
        boardRotationElement.value = settings.boardRotation
        setBoardRotation(settings.boardRotation);
      }
      break;
    default:
      break;
  }
  if (e.altKey) {
    switch (e.key) {
      case "f":
        focusFilterField();
        e.preventDefault();
        break;
      case "r":
        focusRefLookupField();
        e.preventDefault();
        break;
      case "z":
        changeBomLayout("bom-only");
        e.preventDefault();
        break;
      case "x":
        changeBomLayout("left-right");
        e.preventDefault();
        break;
      case "c":
        changeBomLayout("top-bottom");
        e.preventDefault();
        break;
      case "v":
        changeCanvasLayout("F");
        e.preventDefault();
        break;
      case "b":
        changeCanvasLayout("FB");
        e.preventDefault();
        break;
      case "n":
        changeCanvasLayout("B");
        e.preventDefault();
        break;
      default:
        break;
    }
    if (e.key >= '1' && e.key <= '9') {
      toggleBomCheckbox(currentHighlightedRowId, parseInt(e.key));
      e.preventDefault();
    }
  }
}

function hideNetlistButton() {
  document.getElementById("bom-ungrouped-btn").classList.remove("middle-button");
  document.getElementById("bom-ungrouped-btn").classList.add("right-most-button");
  document.getElementById("bom-netlist-btn").style.display = "none";
}

function topToggle() {
  var top = document.getElementById("top");
  var toptoggle = document.getElementById("toptoggle");
  if (top.style.display === "none") {
    top.style.display = "flex";
    toptoggle.classList.remove("flipped");
  } else {
    top.style.display = "none";
    toptoggle.classList.add("flipped");
  }
}

window.onload = function (e) {
  initRender();
  initStorage();
  initDefaults();
  initUtils();
  cleanGutters();
  populateMetadata();
  dbgdiv = document.getElementById("dbg");
  bom = document.getElementById("bombody");
  bomhead = document.getElementById("bomhead");
  filter = "";
  reflookup = "";
  if (!("nets" in pcbdata)) {
    hideNetlistButton();
  }
  initDone = true;
  setBomCheckboxes(document.getElementById("bomCheckboxes").value);

  // Sync UI for rainbow mode and highlight all
  if (document.getElementById("rainbowModeCheckbox")) {
    document.getElementById("rainbowModeCheckbox").checked = settings.rainbowMode;
    var highlightAllLabel = document.getElementById("highlightAllLabel");
    if (highlightAllLabel) {
      highlightAllLabel.style.display = settings.rainbowMode ? "" : "none";
    }
    var showUnitsLabel = document.getElementById("showUnitsLabel");
    if (showUnitsLabel) {
      showUnitsLabel.style.display = settings.rainbowMode ? "" : "none";
    }
  }
  if (document.getElementById("highlightAllCheckbox")) {
    document.getElementById("highlightAllCheckbox").checked = settings.highlightAll;
  }
  if (document.getElementById("showUnitsCheckbox")) {
    document.getElementById("showUnitsCheckbox").checked = settings.showUnits;
  }

  // Triggers render
  changeBomLayout(settings.bomlayout);

  // Users may leave fullscreen without touching the checkbox. Uncheck.
  document.addEventListener('fullscreenchange', () => {
    if (!document.fullscreenElement)
      document.getElementById('fullscreenCheckbox').checked = false;
  });
}


window.onresize = resizeAll;
window.matchMedia("print").addEventListener("change", resizeAll);