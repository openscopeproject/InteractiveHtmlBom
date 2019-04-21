# pcbdata struct

This document describes pcbdata json structure that plugin
extracts from PCB file and injects into generated bom page.

```js
pcbdata = {
   // Describes bounding box of all edge cut drawings.
   // Used for determining default zoom and pan values to fit
   // whole board on canvas.
  "edges_bbox": {
    "minx": 1,
    "miny": 2,
    "maxx": 100,
    "maxy": 200,
  },
  // Describes all edge cut drawings including ones in footprints.
  // See drawing structure description below.
  "edges": [drawing1, drawing2, ...],
  // Contains all drawings + reference + value texts on silkscreen
  // layer grouped by front and back.
  "silkscreen": {
    "F": [drawing1, drawing2, ...],
    "B": [drawing1, drawing2, ...],
  },
  // Same as above but for fabrication layer.
  "fabrication": {
    "F": [drawing1, drawing2, ...],
    "B": [drawing1, drawing2, ...],
  },
  // Describes footprints.
  // See footprint structure description below.
  "modules": [
    footprint1,
    footprint2,
    ...
  ],
  // PCB metadata from the title block.
  "metadata": {
    "title": "title",
    "revision": "rev",
    "company": "Horns and Hoofs",
    "date": "2019-04-18",
  },
  // Contains full bom table as well as filtered by front/back.
  // See bom row description below.
  "bom": {
    "both": [bomrow1, bomrow2, ...],
    "F":  [bomrow1, bomrow2, ...],
    "B":  [bomrow1, bomrow2, ...],
  },
  // Contains parsed stroke data from newstroke font for
  // characters used on the pcb.
  "font_data": {
    "a": {
      "w": character_width,
      // Contains array of polylines that form the character shape.
      "l": [
        [[point1x, point1y], [point2x, point2y],...],
        ...
      ]
    },
    "%": {
      ...
    },
    ...
  },
}
```

# drawing struct

All drawings are either graphical items (arcs, lines, circles)
or text.
Rendering method and properties are determined based on `type`
attribute.


## graphical items

### segment

```js
{
  "type": "segment",
  "start": [x, y],
  "end": end,
  "width": width,
}
```

### circle

```js
{
  "type": "circle",
  "start": [x, y],
  "radius": radius,
  "width": width,
}
```

### arc

```js
{
  "type": "arc",
  "start": [x, y],
  "radius": radius,
  "startangle": angle1,
  "endangle": angle2,
  "width": width,
}
```

### polygon

```js
{
  "type": "polygon",
  "pos": [x, y],
  "angle": angle,
  "polygons": [
    // Polygons are described as set of outlines.
    [
      [point1x, point1y], [point2x, point2y], ...
    ],
    ...
  ]
}
```

## text

```js
{
  "pos": [x, y],
  "text": text,
  "height": height,
  "width": width,
  // -1: justify left
  // 0: justify center
  // 1: justify right
  "horiz_justify": justify,
  "thickness": thickness,
  "attr": [
    // may include none, one or both
    "italic", "mirrored"
  ],
  "angle": angle,
  // Present only if text is reference designator
  "ref": 1,
  // Present only if text is component value
  "val": 1,
}
```

# footprint struct

Footprints are a collection of pads, drawings and some metadata.

```js
{
  "ref": reference,
  "center": [x, y],
  "bbox": {
    "pos": [x, y],
    "size": [x, y],
  },
  "pads": [
    {
      "layers": [
        // Contains one or both
        "F", "B",
      ],
      "pos": [x, y],
      "size": [x, y],
      "angle": angle,
      // Only present if pad is considered first pin.
      // Pins are considered first if it's name is one of
      // 1, A, A1, P1, PAD1
      // OR footprint has no pads named as one of above and
      // current pad's name is lexicographically smallest.
      "pin1": 1,
      // Shape is one of "rect", "oval", "circle", "roundrect", "custom".
      "shape": shape,
      // Only present if shape is "custom".
      "polygons": [
        // Set of polylines same as in polygon drawing.
        [[point1x, point1y], [point2x, point2y], ...],
        ...
      ],
      // Only present if shape is "roundrect".
      "radius": radius,
      // Pad type is "th" for standard and NPTH pads
      // "smd" otherwise.
      "type": type,
      // Present only if type is "th".
      // One of "circle", "oblong".
      "drillshape": drillshape,
      // Optional attribute.
      "offset": [x, y],
    },
    ...
  ],
  "drawings": [
    // Contains only copper F_Cu, B_Cu drawings of the footprint.
    {
      // One of "F", "B".
      "layer": layer,
      // See drawing struct description above.
      "drawing": drawing,
    },
    ...
  ],
  // One of "F", "B".
  "layer": layer,
}
```

# bom row struct

Bom row is a 5-tuple (array in js)

```js
[
  group_component_count,
  value,
  footprint_name,
  reference_set,
  extra_data
]
```

Reference set is array of tuples of (ref, id) where id is just
a unique numeric identifier for each footprint that helps avoid
collisions when references are duplicated.

```js
[
  [reference_name, footprint_id],
  ...
]
```

Extra data is array of extra field data. It's order corresponds
to order of extra field data in config struct.

```js
[field1_value, field2_value, ...]
```

# config struct

```js
config = {
  "dark_mode": bool,
  "show_pads": bool,
  "show_fabrication": bool,
  "show_silkscreen": bool,
  "highlight_pin1": bool,
  "redraw_on_drag": bool,
  "board_rotation": int,
  "checkboxes": "checkbox1,checkbox2,...",
  // One of "bom-only", "left-right", "top-bottom".
  "bom_view": bom_view,
  // One of "F", "FB", "B".
  "layer_view": layer_view,
  "extra_fields": ["field1_name", "field2_name", ...],
}
```
