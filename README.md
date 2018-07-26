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

## So what does it do?

[Demo is worth a thousand words.](https://openscopeproject.org/InteractiveHtmlBomDemo/)

## Installation

KiCad's Pcbnew plugins can be placed in following places, depending on
platform.

-   Windows
    -   `{KICAD_INSTALL_PATH}/share/kicad/scripting`
    -   `{KICAD_INSTALL_PATH}/share/kicad/scripting/plugins`
    -   `%KICAD_PATH%/scripting`
    -   `%KICAD_PATH%/scripting/plugins`
    -   `%APPDATA%/Roaming/kicad/scripting`
    -   `%APPDATA%/Roaming/kicad/scripting/plugins`


-   MacOS
    -   `/Applications/kicad/Kicad/Contents/SharedSupport/scripting/plugins`
    -   `~/Library/Application Support/kicad/scripting/plugins`

I recommend downloading
[latest release](http://github.com/openscopeproject/InteractiveHtmlBom/releases)
or cloning this repo in a directory of your choice and creating a symlink in
one of KiCad's plugin directories to `InteractiveHtmlBom` folder. MacOS users
can do it with `ln -s <target> <link>`, in windows
`cmd /c mklink /D <link> <target>` does the job. If you don't want to bother
with symlinks just copy InteractiveHtmlBom folder into one of plugin
directories.

If you want this plugin to work in all KiCad versions you install, it's
best to put it in user folder (`%APPDATA%` for Windows, `~/` for MacOS).

**Linux users can not install this plugin** at the moment because of
wxPython/GTK3 mess. If you try to do it pcbnew will most likely crash.
This _should_ be fixed in KiCad 5.1.
Meanwhile read on below on how to use it as a standalone script.

## Usage

You can use this plugin as installed Pcbnew Action Plugin or as a standalone
script.

### Installed plugin

Open Pcbnew. Draw your board, make sure it has edges drawn on Edge.Cuts layer.

Save the file and press the
![iBOM](https://raw.githubusercontent.com/openscopeproject/InteractiveHtmlBom/master/InteractiveHtmlBom/icon.png)
button on the top toolbar.

On builds that have plugin menu enabled
`Tools -> External Plugins... -> Generate Interactive HTML BOM` also works.

`bom` folder with generated html bom will be created where the board
file is saved. On Windows html bom page will be automatically opened in default
browser.

### Standalone script

On Linux and MacOS Simply run this in terminal:

```shell
python2 path/to/InteractiveHtmlBom/generate_interactive_bom.py path/to/board.kicad_pcb
```

On windows the trick is to use python that is bundled with KiCad so the command
will look like this:

```shell
path/to/kicad/bin/python.exe .../generate_interactive_bom.py .../board.kicad_pcb
```

## Supported versions

KiCad 5.0 is the only supported version. Pcbnew python interface is not very
stable and tends to have backwards incompatible changes. I will try to support
future versions but generally you can expect my plugin to be tested only on
the latest stable build.

## Known issues

-   Description and Part columns are not supported/tested yet.
-   Circle and Arc shape in edge cuts may lead to incorrect board boundary
    calculation in html render.

    For example a board that is just one circle will not render.

-   Custom shape pads and copper zone drawings in footprints are supported but
    you need patched version of KiCad python bindings.

    Patch is sent to KiCad devs and hopefully will be integrated soon. In the
    meantime you can get prebuilt patched bindings for 5.0
    [here](http://github.com/openscopeproject/InteractiveHtmlBom/releases)
    (win x64 only).

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

1.  KiCad version used.
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

Generated html page is tested in Chrome, Firefox and Edge. IE will not be
supported, patches for other browsers are welcome.

# License and credits

Plugin code is licensed under MIT license, see `LICENSE` for more info.

Html page uses [Split.js](https://github.com/nathancahill/Split.js) library
(also distributed under MIT license) which is embedded into the page.

`units.py` is borrowed from [KiBom](https://github.com/SchrodingersGat/KiBoM)
plugin (MIT license).
