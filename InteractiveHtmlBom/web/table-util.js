/*
 * Table reordering via Drag'n'Drop
 * Inspired by: https://htmldom.dev/drag-and-drop-table-column
 */

function setBomHandlers() {

  const bom = document.getElementById('bomtable');

  let dragName;
  let placeHolderElements;
  let draggingElement;
  let forcePopulation;
  let xOffset;
  let yOffset;
  let wasDragged;

  const mouseUpHandler = function(e) {
    // Delete dragging element
    draggingElement.remove();

    // Make BOM selectable again
    bom.style.removeProperty("userSelect");

    // Remove listeners
    document.removeEventListener('mousemove', mouseMoveHandler);
    document.removeEventListener('mouseup', mouseUpHandler);

    if (wasDragged) {
      // Redraw whole BOM
      populateBomTable();
    }
  }

  const mouseMoveHandler = function(e) {
    // Notice the dragging
    wasDragged = true;

    // Make the dragged element visible
    draggingElement.style.removeProperty("display");

    // Set elements position to mouse position
    draggingElement.style.left = `${e.screenX - xOffset}px`;
    draggingElement.style.top = `${e.screenY - yOffset}px`;

    // Forced redrawing of BOM table
    if (forcePopulation) {
      forcePopulation = false;
      // Copy array
      phe = Array.from(placeHolderElements);
      // populate BOM table again
      populateBomHeader(dragName, phe);
      populateBomBody(dragName, phe);
    }

    // Set up array of hidden columns
    var hiddenColumns = Array.from(settings.hiddenColumns);
    // In the ungrouped mode, quantity don't exist
    if (settings.bommode === "ungrouped")
      hiddenColumns.push("Quantity");
    // If no checkbox fields can be found, we consider them hidden
    if (settings.checkboxes.length == 0)
      hiddenColumns.push("checkboxes");

    // Get table headers and group them into checkboxes, extrafields and normal headers
    const bh = document.getElementById("bomhead");
    headers = Array.from(bh.querySelectorAll("th"))
    headers.shift() // numCol is not part of the columnOrder
    headerGroups = []
    lastCompoundClass = null;
    for (i = 0; i < settings.columnOrder.length; i++) {
      cElem = settings.columnOrder[i];
      if (hiddenColumns.includes(cElem)) {
        // Hidden columns appear as a dummy element
        headerGroups.push([]);
        continue;
      }
      elem = headers.filter(e => getColumnOrderName(e) === cElem)[0];
      if (elem.classList.contains("bom-checkbox")) {
        if (lastCompoundClass === "bom-checkbox") {
          cbGroup = headerGroups.pop();
          cbGroup.push(elem);
          headerGroups.push(cbGroup);
        } else {
          lastCompoundClass = "bom-checkbox";
          headerGroups.push([elem])
        }
      } else {
        headerGroups.push([elem])
      }
    }

    // Copy settings.columnOrder
    var columns = Array.from(settings.columnOrder)

    // Set up array with indices of hidden columns
    var hiddenIndices = hiddenColumns.map(e => settings.columnOrder.indexOf(e));
    var dragIndex = columns.indexOf(dragName);
    var swapIndex = dragIndex;
    var swapDone = false;

    // Check if the current dragged element is swapable with the left or right element
    if (dragIndex > 0) {
      // Get left headers boundingbox
      swapIndex = dragIndex - 1;
      while (hiddenIndices.includes(swapIndex) && swapIndex > 0)
        swapIndex--;
      if (!hiddenIndices.includes(swapIndex)) {
        box = getBoundingClientRectFromMultiple(headerGroups[swapIndex]);
        if (e.clientX < box.left + window.scrollX + (box.width / 2)) {
          swapElement = columns[dragIndex];
          columns.splice(dragIndex, 1);
          columns.splice(swapIndex, 0, swapElement);
          forcePopulation = true;
          swapDone = true;
        }
      }
    }
    if ((!swapDone) && dragIndex < headerGroups.length - 1) {
      // Get right headers boundingbox
      swapIndex = dragIndex + 1;
      while (hiddenIndices.includes(swapIndex))
        swapIndex++;
      if (swapIndex < headerGroups.length) {
        box = getBoundingClientRectFromMultiple(headerGroups[swapIndex]);
        if (e.clientX > box.left + window.scrollX + (box.width / 2)) {
          swapElement = columns[dragIndex];
          columns.splice(dragIndex, 1);
          columns.splice(swapIndex, 0, swapElement);
          forcePopulation = true;
          swapDone = true;
        }
      }
    }

    // Write back change to storage
    if (swapDone) {
      settings.columnOrder = columns
      writeStorage("columnOrder", JSON.stringify(columns));
    }

  }

  const mouseDownHandler = function(e) {
    var target = e.target;
    if (target.tagName.toLowerCase() != "td")
      target = target.parentElement;

    // Used to check if a dragging has ever happened
    wasDragged = false;

    // Create new element which will be displayed as the dragged column
    draggingElement = document.createElement("div")
    draggingElement.classList.add("dragging");
    draggingElement.style.display = "none";
    draggingElement.style.position = "absolute";
    draggingElement.style.overflow = "hidden";

    // Get bomhead and bombody elements
    const bh = document.getElementById("bomhead");
    const bb = document.getElementById("bombody");

    // Get all compound headers for the current column
    var compoundHeaders;
    if (target.classList.contains("bom-checkbox")) {
      compoundHeaders = Array.from(bh.querySelectorAll("th.bom-checkbox"));
    } else {
      compoundHeaders = [target];
    }

    // Create new table which will display the column
    var newTable = document.createElement("table");
    newTable.classList.add("bom");
    newTable.style.background = "white";
    draggingElement.append(newTable);

    // Create new header element
    var newHeader = document.createElement("thead");
    newTable.append(newHeader);

    // Set up array for storing all placeholder elements
    placeHolderElements = [];

    // Add all compound headers to the new thead element and placeholders
    compoundHeaders.forEach(function(h) {
      clone = cloneElementWithDimensions(h);
      newHeader.append(clone);
      placeHolderElements.push(clone);
    });

    // Create new body element
    var newBody = document.createElement("tbody");
    newTable.append(newBody);

    // Get indices for compound headers
    var idxs = compoundHeaders.map(e => getBomTableHeaderIndex(e));

    // For each row in the BOM body...
    var rows = bb.querySelectorAll("tr");
    rows.forEach(function(row) {
      // ..get the cells for the compound column
      const tds = row.querySelectorAll("td");
      var copytds = idxs.map(i => tds[i]);
      // Add them to the new element and the placeholders
      var newRow = document.createElement("tr");
      copytds.forEach(function(td) {
        clone = cloneElementWithDimensions(td);
        newRow.append(clone);
        placeHolderElements.push(clone);
      });
      newBody.append(newRow);
    });

    // Compute width for compound header
    var width = compoundHeaders.reduce((acc, x) => acc + x.clientWidth, 0);
    draggingElement.style.width = `${width}px`;

    // Insert the new dragging element and disable selection on BOM
    bom.insertBefore(draggingElement, null);
    bom.style.userSelect = "none";

    // Determine the mouse position offset
    xOffset = e.screenX - compoundHeaders.reduce((acc, x) => Math.min(acc, x.offsetLeft), compoundHeaders[0].offsetLeft);
    yOffset = e.screenY - compoundHeaders[0].offsetTop;

    // Get name for the column in settings.columnOrder
    dragName = getColumnOrderName(target);

    // Change text and class for placeholder elements
    placeHolderElements = placeHolderElements.map(function(e) {
      newElem = cloneElementWithDimensions(e);
      newElem.textContent = "";
      newElem.classList.add("placeholder");
      return newElem;
    });

    // On next mouse move, the whole BOM needs to be redrawn to show the placeholders
    forcePopulation = true;

    // Add listeners for move and up on mouse
    document.addEventListener('mousemove', mouseMoveHandler);
    document.addEventListener('mouseup', mouseUpHandler);
  }

  // In netlist mode, there is nothing to reorder
  if (settings.bommode === "netlist")
    return;

  // Add mouseDownHandler to every column except the numCol
  bom.querySelectorAll("th")
    .forEach(function(head) {
      if (!head.classList.contains("numCol")) {
        head.onmousedown = mouseDownHandler;
      }
    });

}

function getBoundingClientRectFromMultiple(elements) {
  var elems = Array.from(elements);

  if (elems.length == 0)
    return null;

  var box = elems.shift()
    .getBoundingClientRect();

  elems.forEach(function(elem) {
    var elembox = elem.getBoundingClientRect();
    box.left = Math.min(elembox.left, box.left);
    box.top = Math.min(elembox.top, box.top);
    box.width += elembox.width;
    box.height = Math.max(elembox.height, box.height);
  });

  return box;
}

function cloneElementWithDimensions(elem) {
  var newElem = elem.cloneNode(true);
  newElem.style.height = window.getComputedStyle(elem).height;
  newElem.style.width = window.getComputedStyle(elem).width;
  return newElem;
}

function getBomTableHeaderIndex(elem) {
  const bh = document.getElementById('bomhead');
  const ths = Array.from(bh.querySelectorAll("th"));
  return ths.indexOf(elem);
}

function getColumnOrderName(elem) {
  var cname = elem.getAttribute("col_name");
  if (cname === "bom-checkbox")
    return "checkboxes";
  else
    return cname;
}

function resizableGrid(tablehead) {
  var cols = tablehead.firstElementChild.children;
  var rowWidth = tablehead.offsetWidth;

  for (var i = 1; i < cols.length; i++) {
    if (cols[i].classList.contains("bom-checkbox"))
      continue;
    cols[i].style.width = ((cols[i].clientWidth - paddingDiff(cols[i])) * 100 / rowWidth) + '%';
  }

  for (var i = 1; i < cols.length - 1; i++) {
    var div = document.createElement('div');
    div.className = "column-width-handle";
    cols[i].appendChild(div);
    setListeners(div);
  }

  function setListeners(div) {
    var startX, curCol, nxtCol, curColWidth, nxtColWidth, rowWidth;

    div.addEventListener('mousedown', function(e) {
      e.preventDefault();
      e.stopPropagation();

      curCol = e.target.parentElement;
      nxtCol = curCol.nextElementSibling;
      startX = e.pageX;

      var padding = paddingDiff(curCol);

      rowWidth = curCol.parentElement.offsetWidth;
      curColWidth = curCol.clientWidth - padding;
      nxtColWidth = nxtCol.clientWidth - padding;
    });

    document.addEventListener('mousemove', function(e) {
      if (startX) {
        var diffX = e.pageX - startX;
        diffX = -Math.min(-diffX, curColWidth - 20);
        diffX = Math.min(diffX, nxtColWidth - 20);

        curCol.style.width = ((curColWidth + diffX) * 100 / rowWidth) + '%';
        nxtCol.style.width = ((nxtColWidth - diffX) * 100 / rowWidth) + '%';
        console.log(`${curColWidth + nxtColWidth} ${(curColWidth + diffX) * 100 / rowWidth + (nxtColWidth - diffX) * 100 / rowWidth}`);
      }
    });

    document.addEventListener('mouseup', function(e) {
      curCol = undefined;
      nxtCol = undefined;
      startX = undefined;
      nxtColWidth = undefined;
      curColWidth = undefined
    });
  }

  function paddingDiff(col) {

    if (getStyleVal(col, 'box-sizing') == 'border-box') {
      return 0;
    }

    var padLeft = getStyleVal(col, 'padding-left');
    var padRight = getStyleVal(col, 'padding-right');
    return (parseInt(padLeft) + parseInt(padRight));

  }

  function getStyleVal(elm, css) {
    return (window.getComputedStyle(elm, null).getPropertyValue(css))
  }
}
