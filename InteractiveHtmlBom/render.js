/* PCB rendering code */

var redrawOnDrag = true;

function deg2rad(deg) {
  return deg * Math.PI / 180;
}

function getEdgesBoundaries(edges) {
  var minx = edges.reduce((min, edge) => {
    return Math.min(min, edge.start[0]);
  }, Infinity);
  var maxx = edges.reduce((min, edge) => {
    return Math.max(min, edge.start[0]);
  }, -Infinity);
  var miny = edges.reduce((min, edge) => {
    return Math.min(min, edge.start[1]);
  }, Infinity);
  var maxy = edges.reduce((min, edge) => {
    return Math.max(min, edge.start[1]);
  }, -Infinity);
  return [minx, maxx, miny, maxy];
}

function drawtext(ctx, scalefactor, text, color, flip) {
  ctx.save();
  ctx.translate(...text.pos);
  angle = -text.angle;
  if (flip) {
    ctx.scale(-1, 1);
    angle = -angle;
  }
  txt = text.text.split("\n")
  ctx.rotate(deg2rad(angle));
  ctx.scale(text.width, text.height);
  ctx.fillStyle = color;
  switch (text.horiz_justify) {
    case -1:
      ctx.textAlign = "left";
      break;
    case 0:
      ctx.textAlign = "center";
      break;
    case 1:
      ctx.textAlign = "right";
      break;
  }
  for (i = 0; i < txt.length; i++) {
    offset = -(txt.length - 1) * 0.8 + i * 1.6;
    ctx.fillText(txt[i], 0, offset);
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
    ctx.stroke();
  }
}

function drawOblong(ctx, scalefactor, color, size) {
  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineCap = "round";
  if (size[0] > size[1]) {
    ctx.lineWidth = size[1];
    var from = [-size[0] / 2 + size[1] / 2, 0];
    var to = [-from[0], 0];
  } else {
    ctx.lineWidth = size[0];
    var from = [0, -size[1] / 2 + size[0] / 2];
    var to = [0, -from[1]];
  }
  ctx.moveTo(...from);
  ctx.lineTo(...to);
  ctx.stroke();
}

function drawRoundRect(ctx, scalefactor, color, size, radius) {
  ctx.beginPath();
  ctx.strokeStyle = color;
  x = size[0] * -0.5;
  y = size[1] * -0.5;
  width = size[0];
  height = size[1];
  ctx.moveTo(x, 0);
  ctx.arcTo(x, y + height, x + width, y + height, radius);
  ctx.arcTo(x + width, y + height, x + width, y, radius);
  ctx.arcTo(x + width, y, x, y, radius);
  ctx.arcTo(x, y, x, y + height, radius);
  ctx.closePath();
  ctx.fill();
}

function drawPolygons(ctx, scalefactor, color, polygons) {
  ctx.fillStyle = color;
  for (polygon of polygons) {
    ctx.beginPath();
    for (vertex of polygon) {
      ctx.lineTo(...vertex)
    }
    ctx.closePath();
    ctx.fill();
  }
}

function drawPolygonShape(ctx, scalefactor, shape, color) {
  ctx.save();
  ctx.translate(...shape.pos);
  ctx.rotate(deg2rad(-shape.angle));
  drawPolygons(ctx, scalefactor, color, shape.polygons);
  ctx.restore();
}

function drawDrawing(ctx, layer, scalefactor, drawing, color) {
  if (["segment", "arc", "circle"].includes(drawing.type)) {
    drawedge(ctx, scalefactor, drawing, color);
  } else if (drawing.type == "polygon") {
    drawPolygonShape(ctx, scalefactor, drawing, color);
  } else {
    drawtext(ctx, scalefactor, drawing, color, layer == "B");
  }
}

function drawModule(ctx, layer, scalefactor, module, highlight) {
  var padcolor = "#808080";
  if (highlight) {
    padcolor = "#D04040";
    // draw bounding box
    if (module.layer == layer) {
      ctx.save();
      ctx.globalAlpha = 0.2;
      ctx.translate(...module.bbox.pos);
      ctx.fillStyle = "#D04040";
      ctx.fillRect(
        0, 0,
        ...module.bbox.size);
      ctx.globalAlpha = 1;
      ctx.strokeStyle = "#D04040";
      ctx.lineWidth = 2 / scalefactor;
      ctx.strokeRect(
        0, 0,
        ...module.bbox.size);
      ctx.restore();
    }
  }
  // draw drawings
  for (drawing of module.drawings) {
    if (drawing.layer == layer) {
      drawDrawing(ctx, layer, scalefactor, drawing.drawing, padcolor);
    }
  }
  // draw pads
  for (pad of module.pads) {
    if (pad.layers.includes(layer)) {
      ctx.save();
      ctx.translate(...pad.pos);
      ctx.rotate(deg2rad(pad.angle));
      ctx.fillStyle = padcolor;
      if (pad.shape == "rect") {
        ctx.fillRect(
          ...pad.size.map(c => -c * 0.5),
          ...pad.size);
      } else if (pad.shape == "oval") {
        drawOblong(ctx, scalefactor, padcolor, pad.size)
      } else if (pad.shape == "circle") {
        ctx.beginPath();
        ctx.arc(0, 0, pad.size[0] / 2, 0, 2 * Math.PI);
        ctx.fill();
      } else if (pad.shape == "roundrect") {
        drawRoundRect(ctx, scalefactor, padcolor, pad.size, pad.radius)
      } else if (pad.shape == "custom") {
        drawPolygons(ctx, scalefactor, padcolor, pad.polygons)
      }
      if (pad.type == "th") {
        if (pad.drillshape == "oblong") {
          drawOblong(ctx, scalefactor, "#CCCCCC", pad.drillsize)
        } else {
          ctx.fillStyle = "#CCCCCC"
          ctx.beginPath();
          ctx.arc(0, 0, pad.drillsize[0] / 2, 0, 2 * Math.PI);
          ctx.fill();
        }
      }
      ctx.restore();
    }
  }
}

function drawModules(canvas, layer, scalefactor, highlightedRefs) {
  var ctx = canvas.getContext("2d");
  for (edge of pcbdata.edges) {
    drawedge(ctx, scalefactor, edge, "black");
  }
  for (i in pcbdata.modules) {
    var mod = pcbdata.modules[i];
    var highlight = highlightedRefs.includes(mod.ref);
    drawModule(ctx, layer, scalefactor, mod, highlight);
  }
}

function drawSilkscreen(canvas, layer, scalefactor) {
  var ctx = canvas.getContext("2d");
  for (d of pcbdata.silkscreen[layer]) {
    if (["segment", "arc", "circle"].includes(d.type)) {
      drawedge(ctx, scalefactor, d, "#aa4");
    } else if (d.type == "polygon") {
      drawPolygonShape(ctx, scalefactor, d, "#4aa");
    } else {
      drawtext(ctx, scalefactor, d, "#4aa", layer == "B");
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
  drawModules(canvasdict.highlight, canvasdict.layer, canvasdict.transform.s, highlightedRefs);
}

function drawHighlights() {
  drawHighlightsOnLayer(allcanvas.front);
  drawHighlightsOnLayer(allcanvas.back);
}

function drawBackground(canvasdict) {
  clearCanvas(canvasdict.bg);
  clearCanvas(canvasdict.silk);
  drawModules(canvasdict.bg, canvasdict.layer, canvasdict.transform.s, []);
  drawSilkscreen(canvasdict.silk, canvasdict.layer, canvasdict.transform.s);
}

function prepareCanvas(canvas, flip, transform) {
  var ctx = canvas.getContext("2d");
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  fontsize = 1.55;
  ctx.font = "bold " + fontsize + "px Consolas,\"DejaVu Sans Mono\",Monaco,monospace";
  ctx.textBaseline = "middle";
  ctx.scale(transform.zoom, transform.zoom);
  ctx.translate(transform.panx, transform.pany);
  if (flip) {
    ctx.scale(-1, 1);
  }
  ctx.translate(transform.x, transform.y);
  ctx.scale(transform.s, transform.s);
}

function prepareLayer(canvasdict) {
  flip = (canvasdict.layer == "B");
  for (c of ["bg", "silk", "highlight"]) {
    prepareCanvas(canvasdict[c], flip, canvasdict.transform);
  }
}

function recalcLayerScale(canvasdict) {
  canvasdivid = { "F": "frontcanvas", "B": "backcanvas"}[canvasdict.layer];
  var width = document.getElementById(canvasdivid).clientWidth * 2;
  var height = document.getElementById(canvasdivid).clientHeight * 2;
  var [minx, maxx, miny, maxy] = getEdgesBoundaries(pcbdata.edges);
  var scalefactor = Math.min(
    width * 0.98 / (maxx - minx),
    height * 0.98 / (maxy - miny)
  );
  if (scalefactor < 0) {
    scalefactor = 0.1;
  }
  canvasdict.transform.s = scalefactor;
  flip = (canvasdict.layer == "B");
  if (flip) {
    canvasdict.transform.x = -((maxx + minx) * scalefactor + width) * 0.5;
  } else {
    canvasdict.transform.x = -((maxx + minx) * scalefactor - width) * 0.5;
  }
  canvasdict.transform.y = -((maxy + miny) * scalefactor - height) * 0.5;
  for (c of ["bg", "silk", "highlight"]) {
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
  drawHighlights(layerdict);
  t = layerdict.transform;
  dbgdiv.innerHTML = "x: " + t.x + "</br>y: " + t.y + "</br>s: " + t.s +
    "</br>panx: " + t.panx + "</br>pany: " + t.pany + "</br>zoom: " + t.zoom;
}

function resizeCanvas(layerdict) {
  recalcLayerScale(layerdict);
  redrawCanvas(layerdict);
}

function resizeAll() {
  resizeCanvas(allcanvas.front);
  resizeCanvas(allcanvas.back);
}

function handleMouseDown(e, layerdict) {
  if (e.which != 1) {
    return;
  }
  e.preventDefault();
  e.stopPropagation();
  layerdict.transform.mousestartx = e.offsetX;
  layerdict.transform.mousestarty = e.offsetY;
  layerdict.transform.mousedown = true;
}

function handleMouseUp(e, layerdict) {
  e.preventDefault();
  e.stopPropagation();
  layerdict.transform.mousedown = false;
  if (e.which == 3) {
    // Reset pan and zoom on right click.
    layerdict.transform.panx = 0;
    layerdict.transform.pany = 0;
    layerdict.transform.zoom = 1;
  }
  redrawCanvas(layerdict);
}

function handleMouseMove(e, layerdict) {
  if (!layerdict.transform.mousedown) {
    return;
  }
  e.preventDefault();
  e.stopPropagation();
  dx = e.offsetX - layerdict.transform.mousestartx;
  dy = e.offsetY - layerdict.transform.mousestarty;
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
  t = layerdict.transform;
  var wheeldelta = e.deltaY;
  if (e.deltaMode == 1) {
    // FF only, scroll by lines
    wheeldelta *= 30;
  } else if (e.deltaMode == 2) {
    wheeldelta *= 300;
  }
  if (wheeldelta > 0) {
    m = 100 / wheeldelta;
  } else {
    m = -wheeldelta / 100;
  }
  // Limit amount of zoom per tick.
  if (m > 3) {
    m = 3;
  } else if (m < 0.33) {
    m = 0.33;
  }
  t.zoom *= m;
  zoomd = (1 - m) / t.zoom;
  t.panx += 2 * e.offsetX * zoomd;
  t.pany += 2 * e.offsetY * zoomd;
  redrawCanvas(layerdict);
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
  for (element of [div, layerdict.bg, layerdict.silk, layerdict.highlight]) {
    element.addEventListener("contextmenu", function (e) {
      e.preventDefault();
    }, false);
  }
}

function setRedrawOnDrag(value) {
  redrawOnDrag = value;
  writeStorage("redrawOnDrag", value);
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
