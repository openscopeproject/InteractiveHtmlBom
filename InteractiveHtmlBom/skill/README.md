# Interactive HTML BOM Allegro Skill Script

## Prerequisites
The skill script supports using the `$CDS_SITE` variable, so that the source files needed for the ibom creation, can be stored globally. To use the `$CDS_SITE` variable, add a line `ibom = "path"` to the `site.env` with the `path` pointing to the `InteractiveHtmlBom\web` folder.

If the `site.env` is not used and the files are stored locally, change the `templateDir` in the `ibom` procedure ( `ibom.il` ) to the absolute path of the `web` directory. 

To display text, the `font-data` directory needs to be copied to the `web` directoy. The `font_data` contains all characters needed for the file creation, since the data can not be created dynamically.

If a custom header or footer is needed, copy these files to a folder named `user-files` in the `web` folder. If no files are found or the directory is not existing, these files are skipped during the ibom creation.

To make the skill script available for use, you need to copy the `ibom.il` file to your local skill directory ( usually your installation path + `\share\pcb\etc` ) or the skill directory in the `$CDS_SITE` path. Append it to the `allegro.ilinit` file ( add `load( "path/ibom.il" )` ) or load it manually via the skill load command ( type `set telskill` into the command line and then type `load("ibom.il" )`.

## Usage
If the script is loaded successfully, you can start exporting the interactive bom by typing `ibom + enter` in the command line.
A directory `ibom` is created in your project folder containing the `.html`.

The Script uses the project filename as the project name and asks for the optional arguments `revision` and `company` but you can pass the revision and company name as arguments to the `addMetadata` function by changing the code. The input prompt is than suppressed. To change the default configuration of the interactive bom, you have to look at the `writeConfig` function and the `DATAFORMAT.md`.

## Layer Mapping
Only the following layers are considered for file creation:

| Ibom | Allegro |
| ------| ------ |
| edges | BOARD GEOMETRY/DESIGN_OUTLINE<br>BOARD GEOMETRY/CUTOUT
| Fabrication | PACKAGE GEOMETRY/ASSEMBLY_TOP<br>PACKAGE GEOMETRY/ASSEMBLY_BOTTOM<br>REF DES/ASSEMBLY_TOP<br>REF DES/ASSEMBLY_BOTTOM<br>COMPONENT_VALUE/ASSEMBLY_TOP<br>COMPONENT_VALUE/ASSEMBLY_BOTTOM |
| Silkscreen | PACKAGE GEOMETRY/SILKSCREEN_TOP<br>PACKAGE GEOMETRY/SILKSCREEN_BOTTOM<br>REF DES/SILKSCREEN_TOP<br>REF DES/SILKSCREEN_BOTTOM<br>COMPONENT_VALUE/SILKSCREEN_TOP<br>COMPONENT_VALUE/SILKSCREEN_BOTTOM |

## FONT DATA
The font_data file was created using the `fontParser.py` and the following lines of code:

````
import fontparser as fp
import json

ascii = ' !#$&()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~'

f = open( "font_data", "w" )
fontParser = fp.FontParser()
fontParser.parse_font_for_string( ascii )
chars = fontParser.get_parsed_font()
f.write('"font_data": ')
f.write( json.dumps(chars) )
f.close()
````

## TODO
- components with the same value can not be grouped
- `variants.lst` is not considered, no information about mounted or alternative components
- width of segments ( line, circle, arc ) is fixed to 0.1 at the moment; use the width from the design, in case it is not zero
- fails for large designs ( > 2000 component, > 5.000kB ), because of insufficient memory ( fprintf, writing to file ); fix that, if possible
- ascii characters for `\\` `\"` `\'` `%` caused problems in html rendering 