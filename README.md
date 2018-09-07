# Interactive HTML BOM generation plugin for KiCad EDA

This plugin was born from necessity of generating convenient BOM listing
with ability to easily search for components and their placements on the
pcb.

This is really useful when hand soldering your prototype and you have
to find the 50 places where that 0.1uF cap should be or which of these
SOP8 footprints are for the same micro.

This plugin utilizes Pcbnew python bindings to read pcb data and
render silkscreen, footprint pads, text and drawings. Most of the pcbnew
features are supported but there are some rarely used things that will not
be rendered. For example curve type segments in drawings are not supported.

## So what does it do?

[Demo is worth a thousand words.](https://openscopeproject.org/InteractiveHtmlBomDemo/)

## Installation

### Where to install
KiCad's Pcbnew plugins can be placed in following places, depending on
platform.

-   Windows
    -   `{KICAD_INSTALL_PATH}/share/kicad/scripting/plugins`
    -   `%KICAD_PATH%/scripting/plugins`
    -   `%APPDATA%/Roaming/kicad/scripting/plugins`

-   Linux
    -   `~/.kicad/scripting/plugins`
    -   `~/.kicad_plugins`

-   MacOS
    -   `/Applications/Kicad/kicad.app/Contents/SharedSupport/scripting/plugins`
    -   `~/Library/Application Support/kicad/scripting/plugins` or on newer versions
        `~Library/Preferences/kicad/scripting/plugins`

If a folder does not exist you can create one. Above list may be out of date or
inaccurate for your OS version/distribution. You can get full list of directories
that pcbnew is scanning for plugins by running this in scripting console:
```python
import pcbnew
print pcbnew.PLUGIN_DIRECTORIES_SEARCH
```

### How to install

I recommend downloading
[latest release](http://github.com/openscopeproject/InteractiveHtmlBom/releases)
or cloning this repo in a directory of your choice and creating a symlink in
one of KiCad's plugin directories to `InteractiveHtmlBom` folder. MacOS and Linux
users can do it with `ln -s <target> <link>`, in windows
`cmd /c mklink /D <link> <target>` does the job. If you don't want to bother
with symlinks just copy InteractiveHtmlBom folder into one of plugin
directories.

If you want this plugin to work in all KiCad versions you install, it's
best to put it in user folder (`%APPDATA%` for Windows, `~/` for Linux/MacOS).

Some newer linux distributions have wxpython option in KiCad disabled because of
wxPython/GTK3 mess. In that case you have to try to compile KiCad yourself with
scripting enabled or you can use this plugin from command line.

## Usage

You can use this plugin as installed Pcbnew Action Plugin or as a standalone
script.

### Installed plugin

Open Pcbnew. Draw your board, make sure it has edges drawn on Edge.Cuts layer.

Save the file and press the
![iBOM](https://raw.githubusercontent.com/openscopeproject/InteractiveHtmlBom/master/InteractiveHtmlBom/icon.png)
button on the top toolbar.

If the button is not on the toolbar
`Tools -> External Plugins... -> Generate Interactive HTML BOM` also works.
Note that this menu is only present on builds that have KICAD_SCRIPTING_ACTION_MENU
option turned on. In recent nightly builds you can choose to hide the plugin button in
pcbnew preferences.

`bom` folder with generated html bom will be created where the board
file is saved. Html bom page will be automatically opened in default
browser.

### Standalone script

On Linux simply run this in terminal:

```shell
python2 path/to/InteractiveHtmlBom/generate_interactive_bom.py path/to/board.kicad_pcb
```

On windows the trick is to use python that is bundled with KiCad so the command
will look like this:

```shell
path/to/kicad/bin/python.exe .../generate_interactive_bom.py .../board.kicad_pcb
```

### BOM mouse actions

You can pan the pcb drawings by dragging with left mouse button, zoom using
mouse wheel and reset view by right click.

Left click on a component drawing will highlight corresponding component group,
unless it is currently filtered out by filter or reference lookup fields.
If there are multiple components under mouse cursor, subsequent clicks
will cycle through possible interpretations.

### BOM keyboard shortcuts

Html page supports keyboard shortcuts to perform most tasks:

*  `ArrowUp` / `ArrowDown` scroll through the bom table
*  `Alt-R` focuses reference lookup field
*  `Alt-F` focuses filter field
*  `Alt-Z` switches to bom only view
*  `Alt-X` switches to bom left, drawings right view
*  `Alt-C` switches to bom top, drawings bot view
*  `Alt-V` switches to front only view
*  `Alt-B` switches to front and back view
*  `Alt-N` switches to back only view
*  `Alt-1` through `Alt-9` toggle corresponding checkbox for highlighted bom row
   (if it exists)


## Supported versions

KiCad 5.0 is the only fully supported version. Pcbnew python interface is not very
stable and tends to have backwards incompatible changes. I will try to support
future versions but generally you can expect my plugin to be tested only on
the latest stable build.

Plugin is reported to work with KiCad 4 when used from command line but it can
break any time. If you encounter issues file a bug report and I will try to fix
them if possible but no promises.

## Known issues

-   Description and Part columns are not supported/tested yet.
-   Custom shape pads and copper zone drawings in footprints are supported but
    you need patched version of KiCad python bindings.
    My patch was integrated in KiCad dev branch, if you install a recent nightly
    build custom pads and copper/silkscreen graphics will be rendered.

    You can also get prebuilt patched bindings for windows x64 KiCad 5.0
    [here](http://github.com/openscopeproject/InteractiveHtmlBom/releases).

    Overwrite corresponding files:

    -   `{KICAD_INSTALL_PATH}/bin/_pcbnew.kiface`
    -   `{KICAD_INSTALL_PATH}/lib/python2.7/site-packages/pcbnew.py`
    -   `{KICAD_INSTALL_PATH}/lib/python2.7/site-packages/_pcbnew.pyd`


-   Design is complete and utter shite.

    Sorry about that, not my strong suite. You are welcome to improve it and
    send a PR.

## How to report issues

General software bug reporting rules apply, make sure to describe in most
clear terms the following:

1.  Platform and KiCad version used.
2.  What are the steps to reproduce the issue.
3.  What is the observed behavior.
4.  What is expected behavior.

In most cases I imagine issues will be of 2 types: 1) plugin crashes and nothing
is created and 2) board or parts of it are not rendered correctly.

For the first case you should include stack trace in your bug report. You can
get it by running plugin manually from scripting console.

-   Open pcbnew, go to `Tools -> Scripting Console` or click corresponding
    button.
-   Type following into the console:

    ```python
    from InteractiveHtmlBom import plugin
    plugin.Run()
    ```

    Copy full output into pastebin and add a link to it in your bug report.
    You can skip pastebin if output is small enough (20 lines or less).

For the second case best way to report it is by sharing your kicad_pcb file.
Remove everything that is not relevant to the bug, leave only the part that
is not rendering correctly. That will make it easier for me to debug and
also you won't have to share what is possibly proprietary information.

_Note: don't remove edge cut drawings. You can replace them with a simple box around
problem area._

## Browser support

Generated html page is tested in Chrome and Firefox. IE will not be
supported, patches for other browsers are welcome.

Edge works but saving settings/checkboxes is currently broken because of
https://developer.microsoft.com/en-us/microsoft-edge/platform/issues/8816771/

# License and credits

Plugin code is licensed under MIT license, see `LICENSE` for more info.

Html page uses [Split.js](https://github.com/nathancahill/Split.js) library
(also distributed under MIT license) which is embedded into the page.

`units.py` is borrowed from [KiBom](https://github.com/SchrodingersGat/KiBoM)
plugin (MIT license).
