/* DOM manipulation and misc code */

var bomsplit;
var canvassplit;
var canvaslayout = "default";
var bomlayout = "default";
var initDone = false;
var bomSortFunction = null;
var currentSortColumn = null;
var currentSortOrder = null;
var currentHighlightedRowId;
var highlightHandlers = [];
var moduleIndexToHandler = {};
var highlightedModules = [];
var checkboxes = [];
var bomCheckboxes = "";
var highlightpin1 = false;
var lastClicked;

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
  renderPads = value;
  redrawIfInitDone();
}

function referencesVisible(value) {
  writeStorage("referencesVisible", value);
  renderReferences = value;
  redrawIfInitDone();
}

function valuesVisible(value) {
  writeStorage("valuesVisible", value);
  renderValues = value;
  redrawIfInitDone();
}

function dnpOutline(value) {
  writeStorage("dnpOutline", value);
  renderDnpOutline = value;
  redrawIfInitDone();
}

function setDarkMode(value) {
  if (value) {
    topmostdiv.classList.add("dark");
  } else {
    topmostdiv.classList.remove("dark");
  }
  writeStorage("darkmode", value);
  redrawIfInitDone();
}

function layerVisible(visible, frontCavnas, backCanvas, storageString) {
  var display = (visible) ? "" : "none";
  frontCavnas.style.display = display;
  backCanvas.style.display = display;
  writeStorage(storageString, visible);
}

function fabricationVisible(visible) {
  layerVisible(visible, allcanvas.front.fab, allcanvas.back.fab, "fabricationVisible");
}

function silkscreenVisible(visible) {
  layerVisible(visible, allcanvas.front.silk, allcanvas.back.silk, "silkscreenVisible");
}

function setHighlightPin1(value) {
  writeStorage("highlightpin1", value);
  highlightpin1 = value;
  redrawIfInitDone();
}

function getStoredCheckboxRefs(checkbox) {
  function convert(ref) {
    var intref = parseInt(ref);
    if (isNaN(intref)) {
      for (var i = 0; i < pcbdata.modules.length; i++) {
        if (pcbdata.modules[i].ref == ref) {
          return i;
        }
      }
      return -1;
    } else {
      return intref;
    }
  }
  var existingRefs = readStorage("checkbox_" + checkbox);
  if (!existingRefs) {
    return new Set();
  } else {
    return new Set(existingRefs.split(",").map(r => convert(r)));
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

function createCheckboxChangeHandler(checkbox, references) {
  return function() {
    refsSet = getStoredCheckboxRefs(checkbox);
    if (this.checked) {
      // checkbox ticked
      for (var ref of references) {
        refsSet.add(ref[1]);
      }
    } else {
      // checkbox unticked
      for (var ref of references) {
        refsSet.delete(ref[1]);
      }
    }
    writeStorage("checkbox_" + checkbox, [...refsSet].join(","));
    updateCheckboxStats(checkbox);
  }
}

function createRowHighlightHandler(rowid, refs) {
  return function() {
    if (currentHighlightedRowId) {
      if (currentHighlightedRowId == rowid) {
        return;
      }
      document.getElementById(currentHighlightedRowId).classList.remove("highlighted");
    }
    document.getElementById(rowid).classList.add("highlighted");
    currentHighlightedRowId = rowid;
    highlightedModules = refs.map(r => r[1]);
    drawHighlights();
  }
}

function entryMatches(entry) {
  // check refs
  for (var ref of entry[3]) {
    if (ref[0].toLowerCase().indexOf(filter) >= 0) {
      return true;
    }
  }
  // check extra fields
  for (var i in config.extra_fields) {
    if (entry[4][i].toLowerCase().indexOf(filter) >= 0) {
      return true;
    }
  }
  // check value
  if (entry[1].toLowerCase().indexOf(filter) >= 0) {
    return true;
  }
  // check footprint
  if (entry[2].toLowerCase().indexOf(filter) >= 0) {
    return true;
  }
  return false;
}

function findRefInEntry(entry) {
  return entry[3].filter(r => r[0].toLowerCase() == reflookup);
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

function checkboxSetUnsetAllHandler(checkboxname) {
  return function() {
    var checkboxnum = 0;
    while (checkboxnum < checkboxes.length &&
      checkboxes[checkboxnum].toLowerCase() != checkboxname.toLowerCase()) {
      checkboxnum++;
    }
    if (checkboxnum >= checkboxes.length) {
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

function createColumnHeader(name, cls, comparator) {
  var th = document.createElement("TH");
  th.innerHTML = name;
  th.classList.add(cls);
  th.style.cursor = "pointer";
  var span = document.createElement("SPAN");
  span.classList.add("sortmark");
  span.classList.add("none");
  th.appendChild(span);
  th.onclick = function() {
    if (currentSortColumn && this !== currentSortColumn) {
      // Currently sorted by another column
      currentSortColumn.childNodes[1].classList.remove(currentSortOrder);
      currentSortColumn.childNodes[1].classList.add("none");
      currentSortColumn = null;
      currentSortOrder = null;
    }
    if (currentSortColumn && this === currentSortColumn) {
      // Already sorted by this column
      if (currentSortOrder == "asc") {
        // Sort by this column, descending order
        bomSortFunction = function(a, b) {
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
      currentSortColumn = this;
      currentSortColumn.childNodes[1].classList.remove("none");
      currentSortColumn.childNodes[1].classList.add("asc");
      currentSortOrder = "asc";
    }
    populateBomBody();
  }
  return th;
}

function populateBomHeader() {
  while (bomhead.firstChild) {
    bomhead.removeChild(bomhead.firstChild);
  }
  var tr = document.createElement("TR");
  var th = document.createElement("TH");
  th.classList.add("numCol");
  tr.appendChild(th);
  var checkboxCompareClosure = function(checkbox) {
    return (a, b) => {
      var stateA = getCheckboxState(checkbox, a[3]);
      var stateB = getCheckboxState(checkbox, b[3]);
      if (stateA > stateB) return -1;
      if (stateA < stateB) return 1;
      return 0;
    }
  }
  for (var checkbox of checkboxes) {
    th = createColumnHeader(
      checkbox, "bom-checkbox", checkboxCompareClosure(checkbox));
    th.onclick = fancyDblClickHandler(
      th, th.onclick.bind(th), checkboxSetUnsetAllHandler(checkbox));
    tr.appendChild(th);
  }
  tr.appendChild(createColumnHeader("References", "References", (a, b) => {
    var i = 0;
    while (i < a[3].length && i < b[3].length) {
      if (a[3][i] != b[3][i]) return a[3][i] > b[3][i] ? 1 : -1;
      i++;
    }
    return a[3].length - b[3].length;
  }));
  // Extra fields
  if (config.extra_fields.length > 0) {
    var extraFieldCompareClosure = function(fieldIndex) {
      return (a, b) => {
        var fa = a[4][fieldIndex];
        var fb = b[4][fieldIndex];
        if (fa != fb) return fa > fb ? 1 : -1;
        else return 0;
      }
    }
    for (var i in config.extra_fields) {
      tr.appendChild(createColumnHeader(
        config.extra_fields[i], "extra", extraFieldCompareClosure(i)));
    }
  }
  tr.appendChild(createColumnHeader("Value", "Value", (a, b) => {
    return valueCompare(a[5], b[5], a[1], b[1]);
  }));
  tr.appendChild(createColumnHeader("Footprint", "Footprint", (a, b) => {
    if (a[2] != b[2]) return a[2] > b[2] ? 1 : -1;
    else return 0;
  }));
  tr.appendChild(createColumnHeader("Quantity", "Quantity", (a, b) => {
    return a[3].length - b[3].length;
  }));
  bomhead.appendChild(tr);
}

function populateBomBody() {
  while (bom.firstChild) {
    bom.removeChild(bom.firstChild);
  }
  highlightHandlers = [];
  moduleIndexToHandler = {};
  currentHighlightedRowId = null;
  var first = true;
  switch (canvaslayout) {
    case 'F':
      bomtable = pcbdata.bom.F;
      break;
    case 'FB':
      bomtable = pcbdata.bom.both;
      break;
    case 'B':
      bomtable = pcbdata.bom.B;
      break;
  }
  if (bomSortFunction) {
    bomtable = bomtable.slice().sort(bomSortFunction);
  }
  for (var i in bomtable) {
    var bomentry = bomtable[i];
    if (filter && !entryMatches(bomentry)) {
      continue;
    }
    var references = bomentry[3];
    if (reflookup) {
      references = findRefInEntry(bomentry);
      if (references.length == 0) {
        continue;
      }
    }
    var tr = document.createElement("TR");
    var td = document.createElement("TD");
    var rownum = +i + 1;
    tr.id = "bomrow" + rownum;
    td.textContent = rownum;
    tr.appendChild(td);
    // Checkboxes
    for (var checkbox of checkboxes) {
      if (checkbox) {
        td = document.createElement("TD");
        var input = document.createElement("input");
        input.type = "checkbox";
        input.onchange = createCheckboxChangeHandler(checkbox, references);
        setBomCheckboxState(checkbox, input, references);
        td.appendChild(input);
        tr.appendChild(td);
      }
    }
    // References
    td = document.createElement("TD");
    td.innerHTML = highlightFilter(references.map(r => r[0]).join(", "));
    tr.appendChild(td);
    // Extra fields
    for (var i in config.extra_fields) {
      td = document.createElement("TD");
      td.innerHTML = highlightFilter(bomentry[4][i]);
      tr.appendChild(td);
    }
    // Value
    td = document.createElement("TD");
    td.innerHTML = highlightFilter(bomentry[1]);
    tr.appendChild(td);
    // Footprint
    td = document.createElement("TD");
    td.innerHTML = highlightFilter(bomentry[2]);
    tr.appendChild(td);
    // Quantity
    td = document.createElement("TD");
    td.textContent = bomentry[3].length;
    tr.appendChild(td);
    bom.appendChild(tr);
    var handler = createRowHighlightHandler(tr.id, references);
    tr.onmousemove = handler;
    highlightHandlers.push({
      id: tr.id,
      handler: handler,
      refs: references
    });
    for (var refIndex of references.map(r => r[1])) {
      moduleIndexToHandler[refIndex] = handler;
    }
    if ((filter || reflookup) && first) {
      handler();
      first = false;
    }
  }
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
}

function modulesClicked(moduleIndexes) {
  var lastClickedIndex = moduleIndexes.indexOf(lastClicked);
  for (var i = 1; i <= moduleIndexes.length; i++) {
    var refIndex = moduleIndexes[(lastClickedIndex + i) % moduleIndexes.length];
    if (refIndex in moduleIndexToHandler) {
      lastClicked = refIndex;
      moduleIndexToHandler[refIndex]();
      smoothScrollToRow(currentHighlightedRowId);
      break;
    }
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
      if (bomlayout != "bom-only") {
        canvassplit.collapse(1);
      }
      break;
    case 'B':
      document.getElementById("bl-btn").classList.add("depressed");
      if (bomlayout != "bom-only") {
        canvassplit.collapse(0);
      }
      break;
    default:
      document.getElementById("fb-btn").classList.add("depressed");
      if (bomlayout != "bom-only") {
        canvassplit.setSizes([50, 50]);
      }
  }
  canvaslayout = layout;
  writeStorage("canvaslayout", layout);
  resizeAll();
  populateBomTable();
}

function populateMetadata() {
  document.getElementById("title").innerHTML = pcbdata.metadata.title;
  document.getElementById("revision").innerHTML = "Rev: " + pcbdata.metadata.revision;
  document.getElementById("company").innerHTML = pcbdata.metadata.company;
  document.getElementById("filedate").innerHTML = pcbdata.metadata.date;
  if (pcbdata.metadata.title != "") {
    document.title = pcbdata.metadata.title + " BOM";
  }
  var fp_f = 0, fp_b = 0, pads_f = 0, pads_b = 0, pads_th = 0;
  for (var i = 0; i < pcbdata.modules.length; i++) {
    if (pcbdata.bom.skipped.includes(i)) continue;
    var mod = pcbdata.modules[i];
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
      document.getElementById("bot").style.height = "";
      break;
    case 'top-bottom':
      document.getElementById("tb-btn").classList.add("depressed");
      document.getElementById("frontcanvas").style.display = "";
      document.getElementById("backcanvas").style.display = "";
      document.getElementById("bot").style.height = "calc(100% - 80px)";
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
      document.getElementById("bot").style.height = "calc(100% - 80px)";
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
  bomlayout = layout;
  writeStorage("bomlayout", layout);
  changeCanvasLayout(canvaslayout);
}

function focusFilterField() {
  focusInputField(document.getElementById("filter"));
}

function focusRefLookupField() {
  focusInputField(document.getElementById("reflookup"));
}

function toggleBomCheckbox(bomrowid, checkboxnum) {
  if (!bomrowid || checkboxnum > checkboxes.length) {
    return;
  }
  var bomrow = document.getElementById(bomrowid);
  var checkbox = bomrow.childNodes[checkboxnum].childNodes[0];
  checkbox.checked = !checkbox.checked;
  checkbox.indeterminate = false;
  checkbox.onchange();
}

function checkBomCheckbox(bomrowid, checkboxname) {
  var checkboxnum = 0;
  while (checkboxnum < checkboxes.length &&
    checkboxes[checkboxnum].toLowerCase() != checkboxname.toLowerCase()) {
    checkboxnum++;
  }
  if (!bomrowid || checkboxnum >= checkboxes.length) {
    return;
  }
  var bomrow = document.getElementById(bomrowid);
  var checkbox = bomrow.childNodes[checkboxnum + 1].childNodes[0];
  checkbox.checked = true;
  checkbox.indeterminate = false;
  checkbox.onchange();
}

function setBomCheckboxes(value) {
  bomCheckboxes = value;
  writeStorage("bomCheckboxes", value);
  prepCheckboxes();
  populateBomTable();
}

function prepCheckboxes() {
  checkboxes = bomCheckboxes.split(",").filter((e) => e);
  var table = document.getElementById("checkbox-stats");
  while (table.childElementCount > 1) {
    table.removeChild(table.lastChild);
  }
  if (checkboxes.length) {
    table.style.display = "";
  } else {
    table.style.display = "none";
  }
  for (var checkbox of checkboxes) {
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

function updateCheckboxStats(checkbox) {
  var checked = getStoredCheckboxRefs(checkbox).size;
  var total = pcbdata.modules.length - pcbdata.bom.skipped.length;
  var percent = checked * 100.0 / total;
  var td = document.getElementById("checkbox-stats-" + checkbox);
  td.firstChild.style.width = percent + "%";
  td.lastChild.innerHTML = checked + "/" + total + " (" + Math.round(percent) + "%)";
}

document.onkeydown = function(e) {
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
    }
  }
}

function getStorageBooleanOrDefault(storageString, def) {
  var b = readStorage(storageString);
  if (b === null) {
    b = def;
  } else {
    b = (b == "true");
  }
  return b;
}

function initDefaults() {
  bomlayout = readStorage("bomlayout");
  if (bomlayout === null) {
    bomlayout = config.bom_view;
  }
  if (!['bom-only', 'left-right', 'top-bottom'].includes(bomlayout)) {
    bomlayout = config.bom_view;
  }
  canvaslayout = readStorage("canvaslayout");
  if (canvaslayout === null) {
    canvaslayout = config.layer_view;
  }
  bomCheckboxes = readStorage("bomCheckboxes");
  if (bomCheckboxes === null) {
    bomCheckboxes = config.checkboxes;
  }
  document.getElementById("bomCheckboxes").value = bomCheckboxes;

  var b = getStorageBooleanOrDefault("padsVisible", config.show_pads);
  document.getElementById("padsCheckbox").checked = b;
  padsVisible(b);

  b = getStorageBooleanOrDefault("fabricationVisible", config.show_fabrication);
  document.getElementById("fabricationCheckbox").checked = b;
  fabricationVisible(b);

  b = getStorageBooleanOrDefault("silkscreenVisible", config.show_silkscreen);
  document.getElementById("silkscreenCheckbox").checked = b;
  silkscreenVisible(b);

  b = getStorageBooleanOrDefault("referencesVisible", true);
  document.getElementById("referencesCheckbox").checked = b;
  referencesVisible(b);

  b = getStorageBooleanOrDefault("valuesVisible", true);
  document.getElementById("valuesCheckbox").checked = b;
  valuesVisible(b);

  b = getStorageBooleanOrDefault("dnpOutline", false);
  document.getElementById("dnpOutlineCheckbox").checked = b;
  dnpOutline(b);

  b = getStorageBooleanOrDefault("redrawOnDrag", config.redraw_on_drag);
  document.getElementById("dragCheckbox").checked = b;
  setRedrawOnDrag(b);

  b = getStorageBooleanOrDefault("darkmode", config.dark_mode);
  document.getElementById("darkmodeCheckbox").checked = b;
  setDarkMode(b);

  b = getStorageBooleanOrDefault("highlightpin1", config.highlight_pin1);
  document.getElementById("highlightpin1Checkbox").checked = b;
  setHighlightPin1(b);

  boardRotation = readStorage("boardRotation");
  if (boardRotation === null) {
    boardRotation = config.board_rotation * 5;
  } else {
    boardRotation = parseInt(boardRotation);
  }
  document.getElementById("boardRotation").value = boardRotation / 5;
  document.getElementById("rotationDegree").textContent = boardRotation;
}

window.onload = function(e) {
  initUtils();
  initRender();
  initStorage();
  initDefaults();
  cleanGutters();
  populateMetadata();
  dbgdiv = document.getElementById("dbg");
  bom = document.getElementById("bombody");
  bomhead = document.getElementById("bomhead");
  filter = "";
  reflookup = "";
  initDone = true;
  prepCheckboxes();
  // Triggers render
  changeBomLayout(bomlayout);
}

window.onresize = resizeAll;
window.matchMedia("print").addListener(resizeAll);
