/* PCB rendering code */

var redrawOnDrag = true;
var boardRotation = 0;

function deg2rad(deg) {
  return deg * Math.PI / 180;
}

function calcFontPoint(linepoint, text, offsetx, offsety, tilt) {
  var point = [
    linepoint[0] * text.width + offsetx,
    linepoint[1] * text.height + offsety
  ];
  // Adding half a line height here is technically a bug
  // but pcbnew currently does the same, text is slightly shifted.
  point[0] -= (point[1] + text.height * 0.5) * tilt;
  return point;
}

function drawtext(ctx, text, color, flip) {
  ctx.save();
  ctx.translate(...text.pos);
  var angle = -text.angle;
  if (text.attr.includes("mirrored")) {
    ctx.scale(-1, 1);
    angle = -angle;
  }
  var tilt = 0;
  if (text.attr.includes("italic")) {
    tilt = 0.125;
  }
  var interline = (text.height * 1.5 + text.thickness) / 2;
  var txt = text.text.split("\n");
  ctx.rotate(deg2rad(angle));
  ctx.fillStyle = color;
  ctx.strokeStyle = color;
  ctx.lineCap = "round";
  ctx.lineWidth = text.thickness;
  for (var i in txt) {
    var offsety = (-(txt.length - 1) + i * 2) * interline + text.height / 2;
    var lineWidth = 0;
    for (var c of txt[i]) {
      lineWidth += pcbdata.font_data[c].w * text.width;
    }
    var offsetx = 0;
    switch (text.horiz_justify) {
      case -1:
        // Justify left, do nothing
        break;
      case 0:
        // Justify center
        offsetx -= lineWidth / 2;
        break;
      case 1:
        // Justify right
        offsetx -= lineWidth;
        break;
    }
    for (var c of txt[i]) {
      for (var line of pcbdata.font_data[c].l) {
        // Drawing each segment separately instead of
        // polyline because round line caps don't work in joints
        for (var i = 0; i < line.length - 1; i++) {
          ctx.beginPath();
          ctx.moveTo(...calcFontPoint(line[i], text, offsetx, offsety, tilt));
          ctx.lineTo(...calcFontPoint(line[i + 1], text, offsetx, offsety, tilt));
          ctx.stroke();
        }
      }
      offsetx += pcbdata.font_data[c].w * text.width;
    }
  }
  ctx.restore();
}

function drawedge(ctx, scalefactor, edge, color) {
  ctx.strokeStyle = color;
  ctx.lineWidth = Math.max(1 / scalefactor, edge.width);
  ctx.lineCap = "round";
  if (edge.type == "segment") {
    ctx.beginPath();
    ctx.moveTo(...edge.start);
    ctx.lineTo(...edge.end);
    ctx.stroke();
  }
  if (edge.type == "arc") {
    ctx.beginPath();
    ctx.arc(
      ...edge.start,
      edge.radius,
      deg2rad(edge.startangle),
      deg2rad(edge.endangle));
    ctx.stroke();
  }
  if (edge.type == "circle") {
    ctx.beginPath();
    ctx.arc(
      ...edge.start,
      edge.radius,
      0, 2 * Math.PI);
    ctx.closePath();
    ctx.stroke();
  }
}

function drawRoundRect(ctx, color, size, radius, ctxmethod) {
  ctx.beginPath();
  ctx.strokeStyle = color;
  var x = size[0] * -0.5;
  var y = size[1] * -0.5;
  var width = size[0];
  var height = size[1];
  ctx.moveTo(x, 0);
  ctx.arcTo(x, y + height, x + width, y + height, radius);
  ctx.arcTo(x + width, y + height, x + width, y, radius);
  ctx.arcTo(x + width, y, x, y, radius);
  ctx.arcTo(x, y, x, y + height, radius);
  ctx.closePath();
  ctxmethod();
}

function drawOblong(ctx, color, size, ctxmethod) {
  drawRoundRect(ctx, color, size, Math.min(size[0], size[1]) / 2, ctxmethod);
}

function drawPolygons(ctx, color, polygons, ctxmethod) {
  ctx.fillStyle = color;
  for (var polygon of polygons) {
    ctx.beginPath();
    for (var vertex of polygon) {
      ctx.lineTo(...vertex)
    }
    ctx.closePath();
    ctxmethod();
  }
}

function drawPolygonShape(ctx, shape, color) {
  ctx.save();
  ctx.translate(...shape.pos);
  ctx.rotate(deg2rad(-shape.angle));
  drawPolygons(ctx, color, shape.polygons, ctx.fill.bind(ctx));
  ctx.restore();
}

function drawDrawing(ctx, layer, scalefactor, drawing, color) {
  if (["segment", "arc", "circle"].includes(drawing.type)) {
    drawedge(ctx, scalefactor, drawing, color);
  } else if (drawing.type == "polygon") {
    drawPolygonShape(ctx, drawing, color);
  } else {
    drawtext(ctx, drawing, color, layer == "B");
  }
}

function drawCircle(ctx, radius, ctxmethod) {
  ctx.beginPath();
  ctx.arc(0, 0, radius, 0, 2 * Math.PI);
  ctx.closePath();
  ctxmethod();
}

function drawPad(ctx, pad, color, outline) {
  ctx.save();
  ctx.translate(...pad.pos);
  ctx.rotate(deg2rad(pad.angle));
  if (pad.offset) {
    ctx.translate(...pad.offset);
  }
  ctx.fillStyle = color;
  ctx.strokeStyle = color;
  var ctxmethod = outline ? ctx.stroke.bind(ctx) : ctx.fill.bind(ctx);
  if (pad.shape == "rect") {
    var rect = [...pad.size.map(c => -c * 0.5), ...pad.size];
    if (outline) {
      ctx.strokeRect(...rect);
    } else {
      ctx.fillRect(...rect);
    }
  } else if (pad.shape == "oval") {
    drawOblong(ctx, color, pad.size, ctxmethod);
  } else if (pad.shape == "circle") {
    drawCircle(ctx, pad.size[0] / 2, ctxmethod);
  } else if (pad.shape == "roundrect") {
    drawRoundRect(ctx, color, pad.size, pad.radius, ctxmethod);
  } else if (pad.shape == "custom") {
    drawPolygons(ctx, color, pad.polygons, ctxmethod);
  }
  if (pad.type == "th" && !outline) {
    ctx.fillStyle = "#CCCCCC";
    if (pad.drillshape == "oblong") {
      drawOblong(ctx, "#CCCCCC", pad.drillsize, ctxmethod);
    } else {
      drawCircle(ctx, pad.drillsize[0] / 2, ctxmethod);
    }
  }
  ctx.restore();
}

function drawModule(ctx, layer, scalefactor, module, padcolor, outlinecolor, highlight) {
  if (highlight) {
    // draw bounding box
    if (module.layer == layer) {
      ctx.save();
      ctx.globalAlpha = 0.2;
      ctx.translate(...module.bbox.pos);
      ctx.fillStyle = padcolor;
      ctx.fillRect(
        0, 0,
        ...module.bbox.size);
      ctx.globalAlpha = 1;
      ctx.strokeStyle = padcolor;
      ctx.strokeRect(
        0, 0,
        ...module.bbox.size);
      ctx.restore();
    }
  }
  // draw drawings
  for (var drawing of module.drawings) {
    if (drawing.layer == layer) {
      drawDrawing(ctx, layer, scalefactor, drawing.drawing, padcolor);
    }
  }
  // draw pads
  for (var pad of module.pads) {
    if (pad.layers.includes(layer)) {
      drawPad(ctx, pad, padcolor, false);
      if (pad.pin1 && highlightpin1) {
        drawPad(ctx, pad, outlinecolor, true);
      }
    }
  }
}

function drawEdges(canvas, scalefactor) {
  var ctx = canvas.getContext("2d");
  var edgecolor = getComputedStyle(topmostdiv).getPropertyValue('--pcb-edge-color');
  for (var edge of pcbdata.edges) {
    drawedge(ctx, scalefactor, edge, edgecolor);
  }
}

function drawModules(canvas, layer, scalefactor, highlightedModules) {
  var ctx = canvas.getContext("2d");
  ctx.lineWidth = 3 / scalefactor;
  var style = getComputedStyle(topmostdiv);
  var padcolor = style.getPropertyValue('--pad-color');
  var outlinecolor = style.getPropertyValue('--pin1-outline-color');
  if (highlightedModules.length > 0) {
    padcolor = style.getPropertyValue('--pad-color-highlight');
    outlinecolor = style.getPropertyValue('--pin1-outline-color-highlight');
  }
  for (var i = 0; i < pcbdata.modules.length; i++) {
    var mod = pcbdata.modules[i];
    var highlight = highlightedModules.includes(i);
    if (highlightedModules.length == 0 || highlight) {
      drawModule(ctx, layer, scalefactor, mod, padcolor, outlinecolor, highlight);
    }
  }
}

function drawSilkscreen(canvas, layer, scalefactor) {
  var ctx = canvas.getContext("2d");
  for (var d of pcbdata.silkscreen[layer]) {
    if (["segment", "arc", "circle"].includes(d.type)) {
      drawedge(ctx, scalefactor, d, "#aa4");
    } else if (d.type == "polygon") {
      drawPolygonShape(ctx, d, "#4aa");
    } else {
      drawtext(ctx, d, "#4aa", layer == "B");
    }
  }
}

function clearCanvas(canvas) {
  var ctx = canvas.getContext("2d");
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.restore();
}

function drawHighlightsOnLayer(canvasdict) {
  clearCanvas(canvasdict.highlight);
  drawModules(canvasdict.highlight, canvasdict.layer,
    canvasdict.transform.s, highlightedModules);
}

function drawHighlights() {
  drawHighlightsOnLayer(allcanvas.front);
  drawHighlightsOnLayer(allcanvas.back);
}

function drawBackground(canvasdict) {
  clearCanvas(canvasdict.bg);
  clearCanvas(canvasdict.silk);
  drawEdges(canvasdict.bg, canvasdict.transform.s);
  drawModules(canvasdict.bg, canvasdict.layer, canvasdict.transform.s, []);
  drawSilkscreen(canvasdict.silk, canvasdict.layer, canvasdict.transform.s);
}

function prepareCanvas(canvas, flip, transform) {
  var ctx = canvas.getContext("2d");
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  var fontsize = 1.55;
  ctx.scale(transform.zoom, transform.zoom);
  ctx.translate(transform.panx, transform.pany);
  if (flip) {
    ctx.scale(-1, 1);
  }
  ctx.translate(transform.x, transform.y);
  ctx.rotate(deg2rad(boardRotation));
  ctx.scale(transform.s, transform.s);
}

function prepareLayer(canvasdict) {
  var flip = (canvasdict.layer == "B");
  for (var c of ["bg", "silk", "highlight"]) {
    prepareCanvas(canvasdict[c], flip, canvasdict.transform);
  }
}

function rotateVector(v, angle) {
  angle = deg2rad(angle);
  return [
    v[0] * Math.cos(angle) - v[1] * Math.sin(angle),
    v[0] * Math.sin(angle) + v[1] * Math.cos(angle)
  ];
}

function applyRotation(bbox) {
  var corners = [
    [bbox.minx, bbox.miny],
    [bbox.minx, bbox.maxy],
    [bbox.maxx, bbox.miny],
    [bbox.maxx, bbox.maxy],
  ];
  corners = corners.map((v) => rotateVector(v, boardRotation));
  return {
    minx: corners.reduce((a, v) => Math.min(a, v[0]), Infinity),
    miny: corners.reduce((a, v) => Math.min(a, v[1]), Infinity),
    maxx: corners.reduce((a, v) => Math.max(a, v[0]), -Infinity),
    maxy: corners.reduce((a, v) => Math.max(a, v[1]), -Infinity),
  }
}

function recalcLayerScale(canvasdict) {
  var canvasdivid = {
    "F": "frontcanvas",
    "B": "backcanvas"
  } [canvasdict.layer];
  var width = document.getElementById(canvasdivid).clientWidth * 2;
  var height = document.getElementById(canvasdivid).clientHeight * 2;
  var bbox = applyRotation(pcbdata.edges_bbox);
  var scalefactor = 0.98 * Math.min(
    width / (bbox.maxx - bbox.minx),
    height / (bbox.maxy - bbox.miny)
  );
  if (scalefactor < 0.1) {
    scalefactor = 1;
  }
  canvasdict.transform.s = scalefactor;
  var flip = (canvasdict.layer == "B");
  if (flip) {
    canvasdict.transform.x = -((bbox.maxx + bbox.minx) * scalefactor + width) * 0.5;
  } else {
    canvasdict.transform.x = -((bbox.maxx + bbox.minx) * scalefactor - width) * 0.5;
  }
  canvasdict.transform.y = -((bbox.maxy + bbox.miny) * scalefactor - height) * 0.5;
  for (var c of ["bg", "silk", "highlight"]) {
    canvas = canvasdict[c];
    canvas.width = width;
    canvas.height = height;
    canvas.style.width = (width / 2) + "px";
    canvas.style.height = (height / 2) + "px";
  }
  console.log("Scale factor " + canvasdivid + ": ", canvasdict.transform);
}

function redrawCanvas(layerdict) {
  prepareLayer(layerdict);
  drawBackground(layerdict);
  drawHighlightsOnLayer(layerdict);
}

function resizeCanvas(layerdict) {
  recalcLayerScale(layerdict);
  redrawCanvas(layerdict);
}

function resizeAll() {
  resizeCanvas(allcanvas.front);
  resizeCanvas(allcanvas.back);
}

function bboxScan(layer, x, y) {
  var result = [];
  for (var i = 0; i < pcbdata.modules.length; i++) {
    var module = pcbdata.modules[i];
    if (module.layer == layer) {
      var b = module.bbox;
      if (b.pos[0] <= x && b.pos[0] + b.size[0] >= x &&
        b.pos[1] <= y && b.pos[1] + b.size[1] >= y) {
        result.push(i);
      }
    }
  }
  return result;
}

function handleMouseDown(e, layerdict) {
  if (e.which != 1) {
    return;
  }
  e.preventDefault();
  e.stopPropagation();
  layerdict.transform.mousestartx = e.offsetX;
  layerdict.transform.mousestarty = e.offsetY;
  layerdict.transform.mousedownx = e.offsetX;
  layerdict.transform.mousedowny = e.offsetY;
  layerdict.transform.mousedown = true;
}

function handleMouseClick(e, layerdict) {
  var x = e.offsetX;
  var y = e.offsetY;
  var t = layerdict.transform;
  if (layerdict.layer == "B") {
    x = (2 * x / t.zoom - t.panx + t.x) / -t.s;
  } else {
    x = (2 * x / t.zoom - t.panx - t.x) / t.s;
  }
  y = (2 * y / t.zoom - t.y - t.pany) / t.s;
  var v = rotateVector([x, y], -boardRotation);
  var modules = bboxScan(layerdict.layer, v[0], v[1]);
  if (modules.length > 0) {
    modulesClicked(modules);
    drawHighlights();
  }
}

function handleMouseUp(e, layerdict) {
  e.preventDefault();
  e.stopPropagation();
  if (e.which == 1 &&
    layerdict.transform.mousedown &&
    layerdict.transform.mousedownx == e.offsetX &&
    layerdict.transform.mousedowny == e.offsetY) {
    // This is just a click
    handleMouseClick(e, layerdict);
    layerdict.transform.mousedown = false;
    return;
  }
  if (e.which == 3) {
    // Reset pan and zoom on right click.
    layerdict.transform.panx = 0;
    layerdict.transform.pany = 0;
    layerdict.transform.zoom = 1;
    redrawCanvas(layerdict);
  } else if (!redrawOnDrag) {
    redrawCanvas(layerdict);
  }
  layerdict.transform.mousedown = false;
}

function handleMouseMove(e, layerdict) {
  if (!layerdict.transform.mousedown) {
    return;
  }
  e.preventDefault();
  e.stopPropagation();
  var dx = e.offsetX - layerdict.transform.mousestartx;
  var dy = e.offsetY - layerdict.transform.mousestarty;
  layerdict.transform.panx += 2 * dx / layerdict.transform.zoom;
  layerdict.transform.pany += 2 * dy / layerdict.transform.zoom;
  layerdict.transform.mousestartx = e.offsetX;
  layerdict.transform.mousestarty = e.offsetY;
  if (redrawOnDrag) {
    redrawCanvas(layerdict);
  }
}

function handleMouseWheel(e, layerdict) {
  e.preventDefault();
  e.stopPropagation();
  var t = layerdict.transform;
  var wheeldelta = e.deltaY;
  if (e.deltaMode == 1) {
    // FF only, scroll by lines
    wheeldelta *= 30;
  } else if (e.deltaMode == 2) {
    wheeldelta *= 300;
  }
  var m = Math.pow(1.1, -wheeldelta / 40);
  // Limit amount of zoom per tick.
  if (m > 2) {
    m = 2;
  } else if (m < 0.5) {
    m = 0.5;
  }
  t.zoom *= m;
  var zoomd = (1 - m) / t.zoom;
  t.panx += 2 * e.offsetX * zoomd;
  t.pany += 2 * e.offsetY * zoomd;
  redrawCanvas(layerdict);
  console.log(layerdict.transform.zoom);
}

function addMouseHandlers(div, layerdict) {
  div.onmousedown = function(e) {
    handleMouseDown(e, layerdict);
  };
  div.onmousemove = function(e) {
    handleMouseMove(e, layerdict);
  };
  div.onmouseup = function(e) {
    handleMouseUp(e, layerdict);
  };
  div.onmouseout = function(e) {
    handleMouseUp(e, layerdict);
  }
  div.onwheel = function(e) {
    handleMouseWheel(e, layerdict);
  }
  for (var element of [div, layerdict.bg, layerdict.silk, layerdict.highlight]) {
    element.addEventListener("contextmenu", function(e) {
      e.preventDefault();
    }, false);
  }
}

function setRedrawOnDrag(value) {
  redrawOnDrag = value;
  writeStorage("redrawOnDrag", value);
}

function setBoardRotation(value) {
  boardRotation = value * 5;
  writeStorage("boardRotation", boardRotation);
  document.getElementById("rotationDegree").textContent = boardRotation;
  resizeAll();
}

function initRender() {
  allcanvas = {
    front: {
      transform: {
        x: 0,
        y: 0,
        s: 1,
        panx: 0,
        pany: 0,
        zoom: 1,
        mousestartx: 0,
        mousestarty: 0,
        mousedown: false,
      },
      bg: document.getElementById("F_bg"),
      silk: document.getElementById("F_slk"),
      highlight: document.getElementById("F_hl"),
      layer: "F",
    },
    back: {
      transform: {
        x: 0,
        y: 0,
        s: 1,
        panx: 0,
        pany: 0,
        zoom: 1,
        mousestartx: 0,
        mousestarty: 0,
        mousedown: false,
      },
      bg: document.getElementById("B_bg"),
      silk: document.getElementById("B_slk"),
      highlight: document.getElementById("B_hl"),
      layer: "B",
    }
  };
  addMouseHandlers(document.getElementById("frontcanvas"), allcanvas.front);
  addMouseHandlers(document.getElementById("backcanvas"), allcanvas.back);
}
