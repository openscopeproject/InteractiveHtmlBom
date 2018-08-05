/* DOM manipulation and misc code */

var storagePrefix = 'KiCad_HTML_BOM__' + pcbdata.metadata.title + '__' +
  pcbdata.metadata.revision + '__';
var bomsplit;
var canvassplit;
var canvaslayout = "default";
var bomlayout = "default";
var highlightedRefs = [];

function readStorage(key) {
  return window.localStorage.getItem(storagePrefix + '#' + key);
}

function writeStorage(key, value) {
  window.localStorage.setItem(storagePrefix + '#' + key, value);
}

function dbg(str) {
  dbgdiv.textContent = str;
}

function createRowMouseEnterHandler(refs) {
  return function() {
    highlightedRefs = refs;
    drawHighlights();
  }
}

function entryMatches(entry) {
  // check refs
  for (ref of entry[3]) {
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
  for (ref of entry[3]) {
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
  for (i in parts) {
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

function populateBomTable() {
  while (bom.firstChild) {
    bom.removeChild(bom.firstChild);
  }
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
  for (i in bomtable) {
    var bomentry = bomtable[i];
    if (filter && !entryMatches(bomentry)) {
      continue;
    }
    references = bomentry[3];
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
    tr.onmouseenter = createRowMouseEnterHandler(references);
    if ((filter || reflookup) && first) {
      highlightedRefs = references;
      drawHighlights();
      first = false;
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
  populateBomTable(layout);
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

function removeGutterNode(node) {
  for (i = 0; i < node.childNodes.length; i++) {
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

window.onload = function(e) {
  cleanGutters();
  initRender();
  dbgdiv = document.getElementById("dbg");
  bom = document.getElementById("bombody");
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
  changeBomLayout(bomlayout);
  if (readStorage("silkscreenVisible") === "false") {
    document.getElementById("silkscreenCheckbox").checked = false;
    silkscreenVisible(false);
  }
}

window.onresize = resizeAll;
window.matchMedia("print").addListener(resizeAll);
