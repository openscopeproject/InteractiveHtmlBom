@echo off
set pathofEDASourceFile=%1
echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------
echo                                                                                                                                                                                    -
echo                                  Thank you for using InteractiveHtmlBom
echo                           https://github.com/openscopeproject/InteractiveHtmlBom
echo                                         Bat file by Scarrrr0725
echo                                                                                                                                                                                    -
echo --------------------------------------------------------------------------------------------------------------------
echo --------------------------------------------------------------------------------------------------------------------

::delete --show-dialog after frist start up and setting
set option=--show-dialog

set FilePath=%~dp0
set pyFilePath=%FilePath%generate_interactive_bom.py

:convert
if not defined pathofEDASourceFile (
	set /p pathofEDASourceFile=Please Drag the EasyEDA PCB source file here :
) 
echo  Converting. . . . . . . . . .
python %pyFilePath% %pathofEDASourceFile% %option%

echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------
echo                                                                                                                                                                                    -
echo                                 EDA source file is converted to bom successfully!
echo                                                                                                                                                                                    -
echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------

CHOICE /C YN /N /M "Do you want to convert another file? [Y/N"
	if errorlevel 2 exit
	if errorlevel 1 goto convert
