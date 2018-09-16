/* DOM manipulation and misc code */

var storagePrefix = 'KiCad_HTML_BOM__' + pcbdata.metadata.title + '__' +
  pcbdata.metadata.revision + '__';
var bomsplit;
var canvassplit;
var canvaslayout = "default";
var bomlayout = "default";
var bomSortFunction = null;
var currentSortColumn = null;
var currentSortOrder = null;
var currentHighlightedRowId;
var highlightHandlers = [];
var highlightedRefs = [];
var checkboxes = [];
var bomCheckboxes = "";
var highlightpin1 = false;
var storage;
var lastClickedRef;

function initStorage(key) {
  try {
    window.localStorage.getItem("blank");
    storage = window.localStorage;
  } catch (e) {
    // localStorage not available
  }
  if (!storage) {
    try {
      window.sessionStorage.getItem("blank");
      storage = window.sessionStorage;
    } catch (e) {
      // sessionStorage also not available
    }
  }
}

function readStorage(key) {
  if (storage) {
    return storage.getItem(storagePrefix + '#' + key);
  } else {
    return null;
  }
}

function writeStorage(key, value) {
  if (storage) {
    storage.setItem(storagePrefix + '#' + key, value);
  }
}

function dbg(html) {
  dbgdiv.innerHTML = html;
}

function setDarkMode(value) {
  if (value) {
    topmostdiv.classList.add("dark");
  } else {
    topmostdiv.classList.remove("dark");
  }
  writeStorage("darkmode", value);
  redrawCanvas(allcanvas.front);
  redrawCanvas(allcanvas.back);
}

function setHighlightPin1(value) {
  writeStorage("highlightpin1", value);
  highlightpin1 = value;
  redrawCanvas(allcanvas.front);
  redrawCanvas(allcanvas.back);
}

function getStoredCheckboxRefs(checkbox) {
  var existingRefs = readStorage("checkbox_" + checkbox);
  if (!existingRefs) {
    return new Set();
  } else {
    return new Set(existingRefs.split(","));
  }
}

function getCheckboxState(checkbox, references) {
  var storedRefsSet = getStoredCheckboxRefs(checkbox);
  var currentRefsSet = new Set(references);
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
        refsSet.add(ref);
      }
    } else {
      // checkbox unticked
      for (var ref of references) {
        refsSet.delete(ref);
      }
    }
    writeStorage("checkbox_" + checkbox, [...refsSet].join(","));
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
    highlightedRefs = refs;
    drawHighlights();
  }
}

function entryMatches(entry) {
  // check refs
  for (var ref of entry[3]) {
    if (ref.toLowerCase().indexOf(filter) >= 0) {
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
  for (var ref of entry[3]) {
    if (ref.toLowerCase() == reflookup) {
      return [ref];
    }
  }
  return false;
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

function fancyDblClickHandler(el, onsingle, ondouble) {
  return function() {
    if (el.getAttribute("data-dblclick") == null) {
      el.setAttribute("data-dblclick", 1);
      setTimeout(function() {
        if (el.getAttribute("data-dblclick") == 1) {
          onsingle();
        }
        el.removeAttribute("data-dblclick");
      }, 200);
    } else {
      el.removeAttribute("data-dblclick");
      ondouble();
    }
  }
}

function populateBomHeader() {
  while (bomhead.firstChild) {
    bomhead.removeChild(bomhead.firstChild);
  }
  var tr = document.createElement("TR");
  var th = document.createElement("TH");
  th.classList.add("numCol");
  tr.appendChild(th);
  checkboxes = bomCheckboxes.split(",").filter((e) => e);
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
  tr.appendChild(createColumnHeader("Value", "Value", (a, b) => {
    if (a[1] != b[1]) return a[1] > b[1] ? 1 : -1;
    else return 0;
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
      if (!references) {
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
    td.innerHTML = highlightFilter(references.join(", "));
    tr.appendChild(td);
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
    if ((filter || reflookup) && first) {
      handler();
      first = false;
    }
  }
}

function smoothScrollToRow(rowid) {
  document.getElementById(rowid).scrollIntoView({
    behavior: "smooth",
    block: "center",
    inline: "nearest"
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
}

function modulesClicked(references) {
  var lastClickedIndex = references.indexOf(lastClickedRef);
  var ref = references[(lastClickedIndex + 1) % references.length];
  for (var handler of highlightHandlers) {
    if (handler.refs.indexOf(ref) >= 0) {
      lastClickedRef = ref;
      handler.handler();
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

function silkscreenVisible(visible) {
  if (visible) {
    allcanvas.front.silk.style.display = "";
    allcanvas.back.silk.style.display = "";
    writeStorage("silkscreenVisible", true);
  } else {
    allcanvas.front.silk.style.display = "none";
    allcanvas.back.silk.style.display = "none";
    writeStorage("silkscreenVisible", false);
  }
}

function changeCanvasLayout(layout) {
  document.getElementById("fl-btn").classList.remove("depressed");
  document.getElementById("fb-btn").classList.remove("depressed");
  document.getElementById("bl-btn").classList.remove("depressed");
  switch (layout) {
    case 'F':
      document.getElementById("fl-btn").classList.add("depressed");
      if (bomlayout != "BOM") {
        canvassplit.collapse(1);
      }
      break;
    case 'B':
      document.getElementById("bl-btn").classList.add("depressed");
      if (bomlayout != "BOM") {
        canvassplit.collapse(0);
      }
      break;
    default:
      document.getElementById("fb-btn").classList.add("depressed");
      if (bomlayout != "BOM") {
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
}

function changeBomLayout(layout) {
  document.getElementById("bom-btn").classList.remove("depressed");
  document.getElementById("lr-btn").classList.remove("depressed");
  document.getElementById("tb-btn").classList.remove("depressed");
  switch (layout) {
    case 'BOM':
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
    case 'TB':
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
    case 'LR':
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

function focusInputField(input) {
  input.scrollIntoView(false);
  input.focus();
  input.select();
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


function removeGutterNode(node) {
  for (var i = 0; i < node.childNodes.length; i++) {
    if (node.childNodes[i].classList &&
      node.childNodes[i].classList.contains("gutter")) {
      node.removeChild(node.childNodes[i]);
      break;
    }
  }
}

function cleanGutters() {
  removeGutterNode(document.getElementById("bot"));
  removeGutterNode(document.getElementById("canvasdiv"));
}

function setBomCheckboxes(value) {
  bomCheckboxes = value;
  writeStorage("bomCheckboxes", value);
  populateBomTable();
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
        changeBomLayout("BOM");
        e.preventDefault();
        break;
      case "x":
        changeBomLayout("LR");
        e.preventDefault();
        break;
      case "c":
        changeBomLayout("TB");
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

window.onload = function(e) {
  initStorage();
  cleanGutters();
  initRender();
  dbgdiv = document.getElementById("dbg");
  bom = document.getElementById("bombody");
  bomhead = document.getElementById("bomhead");
  bomlayout = readStorage("bomlayout");
  if (!bomlayout) {
    bomlayout = "LR";
  }
  canvaslayout = readStorage("canvaslayout");
  if (!canvaslayout) {
    canvaslayout = "FB";
  }
  filter = "";
  reflookup = "";
  populateMetadata();
  bomCheckboxes = readStorage("bomCheckboxes");
  if (bomCheckboxes === null) {
    bomCheckboxes = "Sourced,Placed";
  }
  document.getElementById("bomCheckboxes").value = bomCheckboxes;
  if (readStorage("silkscreenVisible") === "false") {
    document.getElementById("silkscreenCheckbox").checked = false;
    silkscreenVisible(false);
  }
  if (readStorage("redrawOnDrag") === "false") {
    document.getElementById("dragCheckbox").checked = false;
    setRedrawOnDrag(false);
  }
  if (readStorage("darkmode") === "true") {
    document.getElementById("darkmodeCheckbox").checked = true;
    setDarkMode(true);
  }
  if (readStorage("highlightpin1") === "true") {
    document.getElementById("highlightpin1Checkbox").checked = true;
    setHighlightPin1(true);
  }
  boardRotation = readStorage("boardRotation");
  if (boardRotation === null) {
    boardRotation = 0;
  } else {
    boardRotation = parseInt(boardRotation);
  }
  document.getElementById("boardRotation").value = boardRotation / 5;
  document.getElementById("rotationDegree").textContent = boardRotation;
  // Triggers render
  changeBomLayout(bomlayout);
}

window.onresize = resizeAll;
window.matchMedia("print").addListener(resizeAll);
