@echo off
set pathofEDASourceFile=%1

::delete --show-dialog after frist start up and setting
set option=--show-dialog

::detect current language of user code of chinese:0804(zh-cn),0404(zh-tw),1004(zh-sg),0C04(zh-hk)
for /f "delims=" %%a in ('reg query "HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\Control\Nls\Language" /v InstallLanguage ^| findstr "0804"') do set language=%%a
set language=%language:~33,37%
if  "%language%"=="0804" (set language=zh) else if  "%language%"=="0404" (set language=zh) else if  "%language%"=="1004" (set language=zh) else if  /i "%language%"=="0C04" (set language=zh) else (set language=en)
if %language%==en (
	call .\i18n\en_UK\language_en.bat
) else (
	set PYTHONIOENCODING=utf-8
	chcp 65001
	call .\i18n\zh_CN\language_zh.bat
)
echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------
echo                                                                                                                                                                                    -
echo                                        %thx4using%                                              
echo                                                     %author%          
echo                                 %gitAddr%                              
echo                                                  %batScar%
echo                                                                                                                                                                                    -
echo --------------------------------------------------------------------------------------------------------------------
echo --------------------------------------------------------------------------------------------------------------------


set FilePath=%~dp0
set pyFilePath=%FilePath%generate_interactive_bom.py

:convert
if not defined pathofEDASourceFile (
	set /p pathofEDASourceFile=%draghere%
) 
echo .
echo  %converting%
echo .
python %pyFilePath% %pathofEDASourceFile% %option%
set pathofEDASourceFile=

echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------
echo .                                                                                                                                                                                   -
echo                                   %converted%
echo .                                                                                                                                                                                   -
echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------


CHOICE /C YN /N /M "%again% [ Y/N ]"
	if errorlevel 2 exit
	if errorlevel 1 goto convert
