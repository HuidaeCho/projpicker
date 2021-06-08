:: install.bat
:: Author: Owen Smith
:: Purpose: projpicker ArcGIS Pro tool box installation

:: Launch folder selection
:: https://stackoverflow.com/a/15885133/1683264
@echo off
setlocal

set "psCommand="(new-object -COM 'Shell.Application')^
.BrowseForFolder(0,'Please choose a folder.',0,0).self.path""

for /f "usebackq delims=" %%I in (`powershell %psCommand%`) do set "folder=%%I"

setlocal enabledelayedexpansion

:: Exit if cancel
IF [!folder!] == [] exit 0
echo Installing projpicker.pyt at !folder!

:: Get files with curl (available on existing windows installs) and install
:: pyt file
curl.exe --output !folder!\projpicker.pyt --url https://raw.githubusercontent.com/HuidaeCho/projpicker/main/guis/arcgispro/projpicker.pyt

:: Latest git
curl.exe -OL --output !folder! --url https://github.com/HuidaeCho/projpicker/archive/main.zip

:: Extract root
tar -xf !folder!/main.zip

:: Move module to main folder
move !folder!/projpicker-main/projpicker !folder!/projpicker

:: clean up
Rmdir /Q /S "!folder!/projpicker-main"
echo !folder!/main.zip
del /f /q "!folder!/main.zip"

endlocal
