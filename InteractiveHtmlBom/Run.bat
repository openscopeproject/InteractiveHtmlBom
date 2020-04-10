@echo off

echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------
echo                                                                                                                                                                                    -
echo                                  Thankyou For Using Generate InteractiveBom
echo                                              Powered By Qu1ck
echo                                Bat Version : Powered By Scarrrr0725
echo                                                                                                                                                                                    -
echo --------------------------------------------------------------------------------------------------------------------
echo --------------------------------------------------------------------------------------------------------------------

::delete --show-dialog after frist sart up and setting
set option=--show-dialog

set FilePath=%~dp0
set pyFilePath=%FilePath%generate_interactive_bom.py

:convert
set /p pathofEDASourceFile=Please Drag the EasyEDA PCB source file here :

echo  Converting. . . . . . . . . .
python %pyFilePath% %pathofEDASourceFile% %option%
echo %pyFilePath% %pathofEDASourceFile%%option%

echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------
echo                                                                                                                                                                                    -
echo                              EDA Source File is Converted  to Bom Successfully ! ! ! !
echo                                    Thankyou For Using Generate InteractiveBom
echo                                                                                                                                                                                    -
echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------

CHOICE /C YN /N /M "Do you Want to Convert Next File  ? [Y/N]"
	if errorlevel 2 exit
	if errorlevel 1 goto convert
