@echo off

set language=zh
::supported language :English and Chinese-Simplified

::delete --show-dialog after frist start up and setting
set option=--show-dialog

set FilePath=%~dp0
set pyFilePath=%FilePath%generate_interactive_bom.py

if %language%==en (
	call :startupEcho_en
	goto:convert_en

) else (
	set PYTHONIOENCODING=utf-8
	chcp 65001
	call :startupEcho_zh
	goto:convert_zh
)


:convert_en

set /p pathofEDASourceFile=Please Drag the EasyEDA PCB source file here :

echo .
echo  Converting. . . . . . . . . .
echo .

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

echo .
echo  导出中. . . . . . . . . .
echo.
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
goto:eof

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
goto:eof
