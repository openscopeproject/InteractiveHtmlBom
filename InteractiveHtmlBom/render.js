/* PCB rendering code */

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
  ctx.translate(...text.pos.map(c => c * scalefactor));
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
  spacing = 1.6 * scalefactor;
  for (i = 0; i < txt.length; i++) {
    offset = -(txt.length - 1) * spacing / 2 + i * spacing;
    ctx.fillText(txt[i], 0, offset);
  }
  ctx.restore();
}

function drawedge(ctx, scalefactor, edge, color) {
  ctx.strokeStyle = color;
  ctx.lineWidth = Math.max(1, edge.width * scalefactor)
  ctx.lineCap = "round";
  if (edge.type == "segment") {
    ctx.beginPath();
    ctx.moveTo(...edge.start.map(c => c * scalefactor));
    ctx.lineTo(...edge.end.map(c => c * scalefactor));
    ctx.stroke();
  }
  if (edge.type == "arc") {
    ctx.beginPath();
    ctx.arc(
      ...edge.start.map(c => c * scalefactor),
      edge.radius * scalefactor,
      deg2rad(edge.startangle),
      deg2rad(edge.endangle));
    ctx.stroke();
  }
  if (edge.type == "circle") {
    ctx.beginPath();
    ctx.arc(
      ...edge.start.map(c => c * scalefactor),
      edge.radius * scalefactor,
      0, 2 * Math.PI);
    ctx.stroke();
  }
}

function drawOblong(ctx, scalefactor, color, size) {
  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineCap = "round";
  if (size[0] > size[1]) {
    ctx.lineWidth = size[1] * scalefactor;
    var from = [-size[0] * scalefactor / 2 + size[1] * scalefactor / 2, 0];
    var to = [-from[0], 0];
  } else {
    ctx.lineWidth = size[0] * scalefactor;
    var from = [0, -size[1] * scalefactor / 2 + size[0] * scalefactor / 2];
    var to = [0, -from[1]];
  }
  ctx.moveTo(...from);
  ctx.lineTo(...to);
  ctx.stroke();
}

function drawRoundRect(ctx, scalefactor, color, size, radius) {
  ctx.beginPath();
  ctx.strokeStyle = color;
  x = size[0] * -0.5 * scalefactor;
  y = size[1] * -0.5 * scalefactor;
  width = size[0] * scalefactor;
  height = size[1] * scalefactor;
  radius = radius * scalefactor;
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
      ctx.lineTo(vertex[0] * scalefactor, vertex[1] * scalefactor)
    }
    ctx.closePath();
    ctx.fill();
  }
}

function drawPolygonShape(ctx, scalefactor, shape, color) {
  ctx.save();
  ctx.translate(...shape.pos.map(c => c * scalefactor));
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
      ctx.translate(...module.bbox.pos.map(c => c * scalefactor));
      ctx.fillStyle = "#D04040";
      ctx.fillRect(
        0, 0,
        ...module.bbox.size.map(c => c * scalefactor));
      ctx.globalAlpha = 1;
      ctx.strokeStyle = "#D04040";
      ctx.lineWidth = 2;
      ctx.strokeRect(
        0, 0,
        ...module.bbox.size.map(c => c * scalefactor));
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
      ctx.translate(...pad.pos.map(c => c * scalefactor));
      ctx.rotate(deg2rad(pad.angle));
      ctx.fillStyle = padcolor;
      if (pad.shape == "rect") {
        ctx.fillRect(
          ...pad.size.map(c => -c * scalefactor * 0.5),
          ...pad.size.map(c => c * scalefactor));
      } else if (pad.shape == "oval") {
        drawOblong(ctx, scalefactor, padcolor, pad.size)
      } else if (pad.shape == "circle") {
        ctx.beginPath();
        ctx.arc(0, 0, pad.size[0] * scalefactor / 2, 0, 2 * Math.PI);
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
          ctx.arc(0, 0, pad.drillsize[0] * scalefactor / 2, 0, 2 * Math.PI);
          ctx.fill();
        }
      }
      ctx.restore();
    }
  }
}

function drawModules(canvas, layer, scalefactor, highlightRefs) {
  var ctx = canvas.getContext("2d");
  for (edge of pcbdata.edges) {
    drawedge(ctx, scalefactor, edge, "black");
  }
  for (i in pcbdata.modules) {
    var mod = pcbdata.modules[i];
    var highlight = highlightRefs.includes(mod.ref);
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

function drawHighlights(highlightRefs) {
  clearCanvas(allcanvas.front.highlight);
  clearCanvas(allcanvas.back.highlight);
  drawModules(allcanvas.front.highlight, "F", frontscale, highlightRefs);
  drawModules(allcanvas.back.highlight, "B", backscale, highlightRefs);
}

function drawBackground() {
  clearCanvas(allcanvas.front.bg);
  clearCanvas(allcanvas.back.bg);
  clearCanvas(allcanvas.front.silk);
  clearCanvas(allcanvas.back.silk);
  drawModules(allcanvas.front.highlight, "F", frontscale, []);
  drawModules(allcanvas.back.highlight, "B", backscale, []);
  drawSilkscreen(allcanvas.front.silk, "F", frontscale);
  drawSilkscreen(allcanvas.back.silk, "B", backscale);
}

function prepareCanvas(canvas, layer, scalefactor, tx, ty) {
  var ctx = canvas.getContext("2d");
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  fontsize = 1.5 * scalefactor;
  ctx.font = "bold " + fontsize + "px Consolas,\"DejaVu Sans Mono\",monospace";
  ctx.textBaseline = "middle";
  if (layer == "F") {
    ctx.translate(tx, ty);
  } else {
    ctx.scale(-1, 1);
    ctx.translate(tx, ty);
  }
}

function resizeLayerCanvas(canvaslist, canvasdivid, layer) {
  var width = document.getElementById(canvasdivid).clientWidth * 2 - 10;
  var height = document.getElementById(canvasdivid).clientHeight * 2 - 10;
  var [minx, maxx, miny, maxy] = getEdgesBoundaries(pcbdata.edges);
  var scalefactor = Math.min(
    width * 0.98 / (maxx - minx),
    height * 0.98 / (maxy - miny)
  );
  if (scalefactor < 0) {
    scalefactor = 0.1;
  }
  console.log("Scale factor " + canvasdivid + ": " + scalefactor)
  if (layer == "B") {
    var tx = -((maxx + minx) * scalefactor + width) * 0.5;
  } else {
    var tx = -((maxx + minx) * scalefactor - width) * 0.5;
  }
  var ty = -((maxy + miny) * scalefactor - height) * 0.5;
  for (c in canvaslist) {
    canvas = canvaslist[c];
    canvas.width = width;
    canvas.height = height;
    canvas.style.width = (width / 2) + "px";
    canvas.style.height = (height / 2) + "px";
    prepareCanvas(canvas, layer, scalefactor, tx, ty);
  }
  return scalefactor;
}

function resizeCanvas() {
  frontscale = resizeLayerCanvas(allcanvas.front, "frontcanvas", "F")
  backscale = resizeLayerCanvas(allcanvas.back, "backcanvas", "B")
  drawBackground();
  drawHighlights([]);
}
