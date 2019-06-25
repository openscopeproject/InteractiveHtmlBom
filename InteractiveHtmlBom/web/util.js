/* Utility functions */

var storagePrefix = 'KiCad_HTML_BOM__' + pcbdata.metadata.title + '__' +
  pcbdata.metadata.revision + '__';
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

function copyToClipboard() {
  var text = '';
  for (var node of bomhead.childNodes[0].childNodes) {
    if (node.firstChild) {
      text = text + node.firstChild.nodeValue;
    }
    if (node != bomhead.childNodes[0].lastChild) {
      text += '\t';
    }
  }
  text += '\n';
  for (var row of bombody.childNodes) {
    for (var cell of row.childNodes) {
      for (var node of cell.childNodes) {
        if (node.nodeName == "INPUT") {
          if (node.checked) {
            text = text + '✓';
          }
        } else if (node.nodeName == "MARK") {
          text = text + node.firstChild.nodeValue;
        } else {
          text = text + node.nodeValue;
        }
      }
      if (cell != row.lastChild) {
        text += '\t';
      }
    }
    text += '\n';
  }
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
  for (var bom_type of ["both", "F", "B"]) {
    for (var row of pcbdata.bom[bom_type]) {
      row.push(parseValue(row[1], row[3][0][0]));
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
