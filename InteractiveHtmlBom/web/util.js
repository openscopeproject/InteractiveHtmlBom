/* Utility functions */

var storagePrefix = 'KiCad_HTML_BOM__' + pcbdata.metadata.title + '__' +
  pcbdata.metadata.revision + '__#';
var storage;

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
    return storage.getItem(storagePrefix + key);
  } else {
    return null;
  }
}

function writeStorage(key, value) {
  if (storage) {
    storage.setItem(storagePrefix + key, value);
  }
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

function smoothScrollToRow(rowid) {
  document.getElementById(rowid).scrollIntoView({
    behavior: "smooth",
    block: "center",
    inline: "nearest"
  });
}

function focusInputField(input) {
  input.scrollIntoView(false);
  input.focus();
  input.select();
}

function saveBomTable(output) {
  var text = '';
  for (var node of bomhead.childNodes[0].childNodes) {
    if (node.firstChild) {
      text += (output == 'csv' ? `"${node.firstChild.nodeValue}"` : node.firstChild.nodeValue);
    }
    if (node != bomhead.childNodes[0].lastChild) {
      text += (output == 'csv' ? ',' : '\t');
    }
  }
  text += '\n';
  for (var row of bombody.childNodes) {
    for (var cell of row.childNodes) {
      let val = '';
      for (var node of cell.childNodes) {
        if (node.nodeName == "INPUT") {
          if (node.checked) {
            val += '✓';
          }
        } else if ((node.nodeName == "MARK") || (node.nodeName == "A")) {
          val += node.firstChild.nodeValue;
        } else {
          val += node.nodeValue;
        }
      }
      if (output == 'csv') {
        val = val.replace(/\"/g, '\"\"'); // pair of double-quote characters
        if (isNumeric(val)) {
          val = +val;                     // use number
        } else {
          val = `"${val}"`;               // enclosed within double-quote
        }
      }
      text += val;
      if (cell != row.lastChild) {
        text += (output == 'csv' ? ',' : '\t');
      }
    }
    text += '\n';
  }

  if (output != 'clipboard') {
    // To file: csv or txt
    var blob = new Blob([text], {
      type: `text/${output}`
    });
    saveFile(`${pcbdata.metadata.title}.${output}`, blob);
  } else {
    // To clipboard
    var textArea = document.createElement("textarea");
    textArea.classList.add('clipboard-temp');
    textArea.value = text;

    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
      if (document.execCommand('copy')) {
        console.log('Bom copied to clipboard.');
      }
    } catch (err) {
      console.log('Can not copy to clipboard.');
    }

    document.body.removeChild(textArea);
  }
}

function isNumeric(str) {
  /* https://stackoverflow.com/a/175787 */
  return (typeof str != "string" ? false : !isNaN(str) && !isNaN(parseFloat(str)));
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

var units = {
  prefixes: {
    giga: ["G", "g", "giga", "Giga", "GIGA"],
    mega: ["M", "mega", "Mega", "MEGA"],
    kilo: ["K", "k", "kilo", "Kilo", "KILO"],
    milli: ["m", "milli", "Milli", "MILLI"],
    micro: ["U", "u", "micro", "Micro", "MICRO", "μ", "µ"], // different utf8 μ
    nano: ["N", "n", "nano", "Nano", "NANO"],
    pico: ["P", "p", "pico", "Pico", "PICO"],
  },
  unitsShort: ["R", "r", "Ω", "F", "f", "H", "h"],
  unitsLong: [
    "OHM", "Ohm", "ohm", "ohms",
    "FARAD", "Farad", "farad",
    "HENRY", "Henry", "henry"
  ],
  getMultiplier: function(s) {
    if (this.prefixes.giga.includes(s)) return 1e9;
    if (this.prefixes.mega.includes(s)) return 1e6;
    if (this.prefixes.kilo.includes(s)) return 1e3;
    if (this.prefixes.milli.includes(s)) return 1e-3;
    if (this.prefixes.micro.includes(s)) return 1e-6;
    if (this.prefixes.nano.includes(s)) return 1e-9;
    if (this.prefixes.pico.includes(s)) return 1e-12;
    return 1;
  },
  valueRegex: null,
}

function initUtils() {
  var allPrefixes = units.prefixes.giga
    .concat(units.prefixes.mega)
    .concat(units.prefixes.kilo)
    .concat(units.prefixes.milli)
    .concat(units.prefixes.micro)
    .concat(units.prefixes.nano)
    .concat(units.prefixes.pico);
  var allUnits = units.unitsShort.concat(units.unitsLong);
  units.valueRegex = new RegExp("^([0-9\.]+)" +
    "\\s*(" + allPrefixes.join("|") + ")?" +
    "(" + allUnits.join("|") + ")?" +
    "(\\b.*)?$", "");
  units.valueAltRegex = new RegExp("^([0-9]*)" +
    "(" + units.unitsShort.join("|") + ")?" +
    "([GgMmKkUuNnPp])?" +
    "([0-9]*)" +
    "(\\b.*)?$", "");
  if (config.fields.includes("Value")) {
    var index = config.fields.indexOf("Value");
    pcbdata.bom["parsedValues"] = {};
    for (var id in pcbdata.bom.fields) {
      pcbdata.bom.parsedValues[id] = parseValue(pcbdata.bom.fields[id][index])
    }
  }
}

function parseValue(val, ref) {
  var inferUnit = (unit, ref) => {
    if (unit) {
      unit = unit.toLowerCase();
      if (unit == 'Ω' || unit == "ohm" || unit == "ohms") {
        unit = 'r';
      }
      unit = unit[0];
    } else {
      ref = /^([a-z]+)\d+$/i.exec(ref);
      if (ref) {
        ref = ref[1].toLowerCase();
        if (ref == "c") unit = 'f';
        else if (ref == "l") unit = 'h';
        else if (ref == "r" || ref == "rv") unit = 'r';
        else unit = null;
      }
    }
    return unit;
  };
  val = val.replace(/,/g, "");
  var match = units.valueRegex.exec(val);
  var unit;
  if (match) {
    val = parseFloat(match[1]);
    if (match[2]) {
      val = val * units.getMultiplier(match[2]);
    }
    unit = inferUnit(match[3], ref);
    if (!unit) return null;
    else return {
      val: val,
      unit: unit,
      extra: match[4],
    }
  }
  match = units.valueAltRegex.exec(val);
  if (match && (match[1] || match[4])) {
    val = parseFloat(match[1] + "." + match[4]);
    if (match[3]) {
      val = val * units.getMultiplier(match[3]);
    }
    unit = inferUnit(match[2], ref);
    if (!unit) return null;
    else return {
      val: val,
      unit: unit,
      extra: match[5],
    }
  }
  return null;
}

function valueCompare(a, b, stra, strb) {
  if (a === null && b === null) {
    // Failed to parse both values, compare them as strings.
    if (stra != strb) return stra > strb ? 1 : -1;
    else return 0;
  } else if (a === null) {
    return 1;
  } else if (b === null) {
    return -1;
  } else {
    if (a.unit != b.unit) return a.unit > b.unit ? 1 : -1;
    else if (a.val != b.val) return a.val > b.val ? 1 : -1;
    else if (a.extra != b.extra) return a.extra > b.extra ? 1 : -1;
    else return 0;
  }
}

function validateSaveImgDimension(element) {
  var valid = false;
  var intValue = 0;
  if (/^[1-9]\d*$/.test(element.value)) {
    intValue = parseInt(element.value);
    if (intValue <= 16000) {
      valid = true;
    }
  }
  if (valid) {
    element.classList.remove("invalid");
  } else {
    element.classList.add("invalid");
  }
  return intValue;
}

function saveImage(layer) {
  var width = validateSaveImgDimension(document.getElementById("render-save-width"));
  var height = validateSaveImgDimension(document.getElementById("render-save-height"));
  var bgcolor = null;
  if (!document.getElementById("render-save-transparent").checked) {
    var style = getComputedStyle(topmostdiv);
    bgcolor = style.getPropertyValue("background-color");
  }
  if (!width || !height) return;

  // Prepare image
  var canvas = document.createElement("canvas");
  var layerdict = {
    transform: {
      x: 0,
      y: 0,
      s: 1,
      panx: 0,
      pany: 0,
      zoom: 1,
    },
    bg: canvas,
    fab: canvas,
    silk: canvas,
    highlight: canvas,
    layer: layer,
  }
  // Do the rendering
  recalcLayerScale(layerdict, width, height);
  prepareLayer(layerdict);
  clearCanvas(canvas, bgcolor);
  drawBackground(layerdict, false);
  drawHighlightsOnLayer(layerdict, false);

  // Save image
  var imgdata = canvas.toDataURL("image/png");

  var filename = pcbdata.metadata.title;
  if (pcbdata.metadata.revision) {
    filename += `.${pcbdata.metadata.revision}`;
  }
  filename += `.${layer}.png`;
  saveFile(filename, dataURLtoBlob(imgdata));
}

function saveSettings() {
  var data = {
    type: "InteractiveHtmlBom settings",
    version: 1,
    pcbmetadata: pcbdata.metadata,
    settings: settings,
  }
  var blob = new Blob([JSON.stringify(data, null, 4)], {
    type: "application/json"
  });
  saveFile(`${pcbdata.metadata.title}.settings.json`, blob);
}

function loadSettings() {
  var input = document.createElement("input");
  input.type = "file";
  input.accept = ".settings.json";
  input.onchange = function(e) {
    var file = e.target.files[0];
    var reader = new FileReader();
    reader.onload = readerEvent => {
      var content = readerEvent.target.result;
      var newSettings;
      try {
        newSettings = JSON.parse(content);
      } catch (e) {
        alert("Selected file is not InteractiveHtmlBom settings file.");
        return;
      }
      if (newSettings.type != "InteractiveHtmlBom settings") {
        alert("Selected file is not InteractiveHtmlBom settings file.");
        return;
      }
      var metadataMatches = newSettings.hasOwnProperty("pcbmetadata");
      if (metadataMatches) {
        for (var k in pcbdata.metadata) {
          if (!newSettings.pcbmetadata.hasOwnProperty(k) || newSettings.pcbmetadata[k] != pcbdata.metadata[k]) {
            metadataMatches = false;
          }
        }
      }
      if (!metadataMatches) {
        var currentMetadata = JSON.stringify(pcbdata.metadata, null, 4);
        var fileMetadata = JSON.stringify(newSettings.pcbmetadata, null, 4);
        if (!confirm(
            `Settins file metadata does not match current metadata.\n\n` +
            `Page metadata:\n${currentMetadata}\n\n` +
            `Settings file metadata:\n${fileMetadata}\n\n` +
            `Press OK if you would like to import settings anyway.`)) {
          return;
        }
      }
      overwriteSettings(newSettings.settings);
    }
    reader.readAsText(file, 'UTF-8');
  }
  input.click();
}

function overwriteSettings(newSettings) {
  initDone = false;
  Object.assign(settings, newSettings);
  writeStorage("bomlayout", settings.bomlayout);
  writeStorage("bommode", settings.bommode);
  writeStorage("canvaslayout", settings.canvaslayout);
  writeStorage("bomCheckboxes", settings.checkboxes.join(","));
  document.getElementById("bomCheckboxes").value = settings.checkboxes.join(",");
  for (var checkbox of settings.checkboxes) {
    writeStorage("checkbox_" + checkbox, settings.checkboxStoredRefs[checkbox]);
  }
  writeStorage("markWhenChecked", settings.markWhenChecked);
  padsVisible(settings.renderPads);
  document.getElementById("padsCheckbox").checked = settings.renderPads;
  fabricationVisible(settings.renderFabrication);
  document.getElementById("fabricationCheckbox").checked = settings.renderFabrication;
  silkscreenVisible(settings.renderSilkscreen);
  document.getElementById("silkscreenCheckbox").checked = settings.renderSilkscreen;
  referencesVisible(settings.renderReferences);
  document.getElementById("referencesCheckbox").checked = settings.renderReferences;
  valuesVisible(settings.renderValues);
  document.getElementById("valuesCheckbox").checked = settings.renderValues;
  tracksVisible(settings.renderTracks);
  document.getElementById("tracksCheckbox").checked = settings.renderTracks;
  zonesVisible(settings.renderZones);
  document.getElementById("zonesCheckbox").checked = settings.renderZones;
  dnpOutline(settings.renderDnpOutline);
  document.getElementById("dnpOutlineCheckbox").checked = settings.renderDnpOutline;
  setRedrawOnDrag(settings.redrawOnDrag);
  document.getElementById("dragCheckbox").checked = settings.redrawOnDrag;
  setDarkMode(settings.darkMode);
  document.getElementById("darkmodeCheckbox").checked = settings.darkMode;
  setHighlightPin1(settings.highlightpin1);
  document.getElementById("highlightpin1Checkbox").checked = settings.highlightpin1;
  writeStorage("boardRotation", settings.boardRotation);
  document.getElementById("boardRotation").value = settings.boardRotation / 5;
  document.getElementById("rotationDegree").textContent = settings.boardRotation;
  setOffsetBackRotation(settings.offsetBackRotation);
  document.getElementById("offsetBackRotationCheckbox").checked = settings.offsetBackRotation;
  initDone = true;
  prepCheckboxes();
  changeBomLayout(settings.bomlayout);
}

function saveFile(filename, blob) {
  var link = document.createElement("a");
  var objurl = URL.createObjectURL(blob);
  link.download = filename;
  link.href = objurl;
  link.click();
}

function dataURLtoBlob(dataurl) {
  var arr = dataurl.split(','),
    mime = arr[0].match(/:(.*?);/)[1],
    bstr = atob(arr[1]),
    n = bstr.length,
    u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new Blob([u8arr], {
    type: mime
  });
}

var settings = {
  canvaslayout: "default",
  bomlayout: "default",
  bommode: "grouped",
  checkboxes: [],
  checkboxStoredRefs: {},
  darkMode: false,
  highlightpin1: false,
  redrawOnDrag: true,
  boardRotation: 0,
  offsetBackRotation: false,
  renderPads: true,
  renderReferences: true,
  renderValues: true,
  renderSilkscreen: true,
  renderFabrication: true,
  renderDnpOutline: false,
  renderTracks: true,
  renderZones: true,
  columnOrder: [],
  hiddenColumns: []
}

function initDefaults() {
  settings.bomlayout = readStorage("bomlayout");
  if (settings.bomlayout === null) {
    settings.bomlayout = config.bom_view;
  }
  if (!['bom-only', 'left-right', 'top-bottom'].includes(settings.bomlayout)) {
    settings.bomlayout = config.bom_view;
  }
  settings.bommode = readStorage("bommode");
  if (settings.bommode === null) {
    settings.bommode = "grouped";
  }
  if (!["grouped", "ungrouped", "netlist"].includes(settings.bommode)) {
    settings.bommode = "grouped";
  }
  settings.canvaslayout = readStorage("canvaslayout");
  if (settings.canvaslayout === null) {
    settings.canvaslayout = config.layer_view;
  }
  var bomCheckboxes = readStorage("bomCheckboxes");
  if (bomCheckboxes === null) {
    bomCheckboxes = config.checkboxes;
  }
  settings.checkboxes = bomCheckboxes.split(",").filter((e) => e);
  document.getElementById("bomCheckboxes").value = bomCheckboxes;

  settings.markWhenChecked = readStorage("markWhenChecked") || "";
  populateMarkWhenCheckedOptions();

  function initBooleanSetting(storageString, def, elementId, func) {
    var b = readStorage(storageString);
    if (b === null) {
      b = def;
    } else {
      b = (b == "true");
    }
    document.getElementById(elementId).checked = b;
    func(b);
  }

  initBooleanSetting("padsVisible", config.show_pads, "padsCheckbox", padsVisible);
  initBooleanSetting("fabricationVisible", config.show_fabrication, "fabricationCheckbox", fabricationVisible);
  initBooleanSetting("silkscreenVisible", config.show_silkscreen, "silkscreenCheckbox", silkscreenVisible);
  initBooleanSetting("referencesVisible", true, "referencesCheckbox", referencesVisible);
  initBooleanSetting("valuesVisible", true, "valuesCheckbox", valuesVisible);
  if ("tracks" in pcbdata) {
    initBooleanSetting("tracksVisible", true, "tracksCheckbox", tracksVisible);
    initBooleanSetting("zonesVisible", true, "zonesCheckbox", zonesVisible);
  } else {
    document.getElementById("tracksAndZonesCheckboxes").style.display = "none";
    tracksVisible(false);
    zonesVisible(false);
  }
  initBooleanSetting("dnpOutline", false, "dnpOutlineCheckbox", dnpOutline);
  initBooleanSetting("redrawOnDrag", config.redraw_on_drag, "dragCheckbox", setRedrawOnDrag);
  initBooleanSetting("darkmode", config.dark_mode, "darkmodeCheckbox", setDarkMode);
  initBooleanSetting("highlightpin1", config.highlight_pin1, "highlightpin1Checkbox", setHighlightPin1);

  var fields = ["checkboxes", "References"].concat(config.fields).concat(["Quantity"]);
  var hcols = JSON.parse(readStorage("hiddenColumns"));
  if (hcols === null) {
    hcols = [];
  }
  settings.hiddenColumns = hcols.filter(e => fields.includes(e));

  var cord = JSON.parse(readStorage("columnOrder"));
  if (cord === null) {
    cord = fields;
  } else {
    cord = cord.filter(e => fields.includes(e));
    if (cord.length != fields.length)
      cord = fields;
  }
  settings.columnOrder = cord;

  settings.boardRotation = readStorage("boardRotation");
  if (settings.boardRotation === null) {
    settings.boardRotation = config.board_rotation * 5;
  } else {
    settings.boardRotation = parseInt(settings.boardRotation);
  }
  document.getElementById("boardRotation").value = settings.boardRotation / 5;
  document.getElementById("rotationDegree").textContent = settings.boardRotation;
  initBooleanSetting("offsetBackRotation", config.offset_back_rotation, "offsetBackRotationCheckbox", setOffsetBackRotation);
}

// Helper classes for user js callbacks.

const IBOM_EVENT_TYPES = {
  ALL: "all",
  HIGHLIGHT_EVENT: "highlightEvent",
  CHECKBOX_CHANGE_EVENT: "checkboxChangeEvent",
  BOM_BODY_CHANGE_EVENT: "bomBodyChangeEvent",
}

const EventHandler = {
  callbacks: {},
  init: function() {
    for (eventType of Object.values(IBOM_EVENT_TYPES))
      this.callbacks[eventType] = [];
  },
  registerCallback: function(eventType, callback) {
    this.callbacks[eventType].push(callback);
  },
  emitEvent: function(eventType, eventArgs) {
    event = {
      eventType: eventType,
      args: eventArgs,
    }
    var callback;
    for (callback of this.callbacks[eventType])
      callback(event);
    for (callback of this.callbacks[IBOM_EVENT_TYPES.ALL])
      callback(event);
  }
}
EventHandler.init();
