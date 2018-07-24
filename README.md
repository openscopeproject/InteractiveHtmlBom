# Interactive HTML BOM generation plugin for KiCad EDA

This plugin was born from necessity of generating convenient BOM listing
with ability to easily search for components and their placements on the
pcb.

This is really useful when hand soldering your prototype and you have
to find the 50 places where that 0.1uF cap should be or which of these
SOP8 footprints are for the same micro.

This plugin utilizes Pcbnew python bindings to read pcb data and
render silkscreen, footprint pads, texts and drawings. Most of the pcbnew
features are supported but there are some rarely used things that will not
be rendered. For example curve type segments in drawings are not supported.

## Installation

KiCad's Pcbnew plugins can be placed in following places, depending on
platform.

-   Windows
    -   {KICAD_INSTALL_PATH}/share/kicad/scripting
    -   {KICAD_INSTALL_PATH}/share/kicad/scripting/plugins
    -   %KICAD_PATH%/scripting
    -   %KICAD_PATH%/scripting/plugins
    -   %APPDATA%/Roaming/kicad/scripting
    -   %APPDATA%/Roaming/kicad/scripting/plugins


-   Linux (some distributions may install in /usr/local instead of /usr)
    -   /usr/share/kicad/scripting
    -   /usr/share/kicad/scripting/plugins
    -   $KICAD_PATH/scripting
    -   $KICAD_PATH/scripting/plugins
    -   ~/.kicad_plugins
    -   ~/.kicad/scripting
    -   ~/.kicad/scripting/plugins


-   MacOS
    -   /Applications/kicad/Kicad/Contents/SharedSupport/scripting/plugins
    -   ~/Library/Application Support/kicad/scripting/plugins

I recommend downloading [latest release](http://github.com/osp/release) or
cloning this repo in a directory of your choice and creating a symlink in one of
KiCad's plugin directories to `InteractiveHtmlBom` folder. Linux users can do
it with `ln -s <target> <link>`, in windows `cmd /c mklink /D <link> <target>`
does the job.

If you want this plugin to work in all KiCad versions you install, it's
best to put it in user folder (%APPDATA% for Windows, ~/ for Linux).

## Usage

Open Pcbnew. Draw your board, make sure it has edges drawn on Edge.Cuts layer.

Save the file and press the
[iBOM](http://github.com/osp/InteractiveHtmlBom/icon.png) button.

## Supported versions

Kicad 5.0 and later are supported.

## Known issues

-   Circle and Arc shape in edge cuts may lead to incorrect board boundary
    calculation in html render.

-   Custom shape pads and copper zone drawings in footprints are supported but
    you need patched version of KiCad python bindings.

    You can get these bindings [here](http://github.com/osp/bindings).

    Overwrite corresponding files:

    -   {KICAD_INSTALL_PATH}/bin/\_pcbnew.kiface
    -   {KICAD_INSTALL_PATH}/lib/python2.7/site-packages/pcbnew.py
    -   {KICAD_INSTALL_PATH}/lib/python2.7/site-packages/\_pcbnew.pyd

    Patch is sent to KiCad devs and hopefully will be integrated soon.

## Browser support

Generated html page is tested in Chrome, Firefox and Edge. IE will not be
supported, patched for other browsers are welcome.

# License and credits

Plugin code is licensed under MIT license, see `LICENSE` for more info.

Html page uses [Split.js](https://github.com/nathancahill/Split.js) library
(also distributed under MIT license) which is embedded into the page.

`units.py` is borrowed from [KiBom](https://github.com/SchrodingersGat/KiBoM)
plugin (MIT license).
