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
