# Interactive HTML BOM plugin for KiCad

This plugin was born from necessity of generating convenient BOM listing with ability to easily search for components and their placements on the pcb.

This is really useful when hand soldering your prototype and you have to find the 50 places where that 0.1uF cap should be or which of these SOP8 footprints are for the same micro. Dynamically highlighting all components in the same group on the rendering of the pcb makes manually populating the board so much easier.

This plugin utilizes Pcbnew python bindings to read pcb data and render silkscreen, footprint pads, text and drawings. Additionally it can pull data from schematic if you export it through netlist file or through xml file that Eeschema can generate from it's internal bom tool. That extra data can be added as additional columns in the BOM table (for example manufacturer id) or it can be used to indicate which components should be omitted altogether (dnp field). For full description of functionality see wiki.

Generated html page is fully self contained, doesn't need internet connection to work and can be packaged with documentation of your project or hosted anywhere on the web.

[Demo is worth a thousand words.](https://openscopeproject.org/InteractiveHtmlBomDemo/)

## Installation and Usage

See [project wiki](https://github.com/openscopeproject/InteractiveHtmlBom/wiki) for instructions.

## License and credits

Plugin code is licensed under MIT license, see `LICENSE` for more info.

Html page uses [Split.js](https://github.com/nathancahill/Split.js) library
(also distributed under MIT license) which is embedded into the page.

`units.py` is borrowed from [KiBom](https://github.com/SchrodingersGat/KiBoM)
plugin (MIT license).
