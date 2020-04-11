@echo off

language=en 
::supported language :English and Chinese-Simplified

::delete --show-dialog after frist start up and setting
set option=--show-dialog

set FilePath=%~dp0
set pyFilePath=%FilePath%generate_interactive_bom.py

if language==en (
	call :convert_en 

)


:convert_en
set /p pathofEDASourceFile=Please Drag the EasyEDA PCB source file here :

echo  Converting. . . . . . . . . .
python %pyFilePath% %pathofEDASourceFile% %option%

echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------
echo                                                                                                                                                                                    -
echo                                 EDA source file is converted to bom successfully!
echo                                                                                                                                                                                    -
echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------

CHOICE /C YN /N /M "Do you want to convert another file? [Y/N]
	if errorlevel 2 exit
	if errorlevel 1 goto convert_en


:convert_zh
set /p pathofEDASourceFile=请将您的EDA PCB源文件拖移至此:

echo  导出中. . . . . . . . . .
python %pyFilePath% %pathofEDASourceFile% %option%

echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------
echo .                                                                                                                                                                                   
echo                                           您的EDA 源文件已成功转换到 Bom ！
echo .                                                                                                                                                                        
echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------

CHOICE /C YN /N /M "请问您还要为其他文件导出BOM吗? [Y/N]
	if errorlevel 2 exit
	if errorlevel 1 goto convert_zh


:startupEcho_en
echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------
echo .                                                                                                                                                                                  -
echo                                  Thank you for using InteractiveHtmlBom
echo                           https://github.com/openscopeproject/InteractiveHtmlBom
echo                                         Bat file by Scarrrr0725
echo .                                                                                                                                                                                  -
echo --------------------------------------------------------------------------------------------------------------------
echo --------------------------------------------------------------------------------------------------------------------

:startupEcho_zh
echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------
echo .                                                                                                                                                  
echo                                          感谢使用 Generate Interactive Bom                                                       
echo                                                   Powered By Qu1ck                                                   
echo                                    Bat ( EasyEDA）版本 : Powered By Scarrrr0725
echo .                                                                                                                                                                 
echo --------------------------------------------------------------------------------------------------------------------
echo --------------------------------------------------------------------------------------------------------------------
