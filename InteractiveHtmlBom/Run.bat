@echo off
set pathofEDASourceFile=%1
set FilePath=%~dp0

::delete --show-dialog after frist start up and setting
set option=--show-dialog

::detect current language of user.
FOR /F "tokens=3" %%a IN ('reg query "HKCU\Control Panel\Desktop" /v PreferredUILanguages ^| find "PreferredUILanguages"') DO set language=%%a
set language=%language:~,2%
if %language%==zh (
	set PYTHONIOENCODING=utf-8
	chcp 65001
	call %FilePath%\i18n\language_zh.bat
) else (
	call %FilePath%\i18n\language_en.bat
)
echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------
echo                                                                                                                                                                                    -
echo %i18n_thx4using%
echo %i18n_gitAddr%
echo %i18n_batScar%
echo                                                                                                                                                                                    -
echo --------------------------------------------------------------------------------------------------------------------
echo --------------------------------------------------------------------------------------------------------------------

set pyFilePath=%FilePath%generate_interactive_bom.py

:convert
if not defined pathofEDASourceFile (
	set /p pathofEDASourceFile=%i18n_draghere%
) 
echo .
echo  %i18n_converting%
echo .
python %pyFilePath% %pathofEDASourceFile% %option%
set pathofEDASourceFile=

echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------
echo .                                                                                                                                                                                   -
echo %i18n_converted%
echo .                                                                                                                                                                                   -
echo -------------------------------------------------------------------------------------------------------------------
echo -------------------------------------------------------------------------------------------------------------------


CHOICE /C YN /N /M "%i18n_again% [ Y/N ]"
	if errorlevel 2 exit
	if errorlevel 1 goto convert
