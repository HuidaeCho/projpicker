:: install.bat
:: Author: Owen Smith
:: Purpose: projpicker ArcGIS Pro tool box installation

@echo off
setlocal

:: Constants
set PYTURL=https://raw.githubusercontent.com/HuidaeCho/projpicker/main/guis/arcgispro/projpicker.pyt
set GITURL=https://github.com/HuidaeCho/projpicker/archive/main.zip


:: Launch folder selection
:: https://stackoverflow.com/a/15885133/1683264
set "psCommand="(new-object -COM 'Shell.Application')^
.BrowseForFolder(0,'Please choose a folder.',0,0).self.path""

for /f "usebackq delims=" %%I in (`powershell %psCommand%`) do set "folder=%%I"

setlocal enabledelayedexpansion

:: Exit if cancel
IF [!folder!] == [] exit 0

:: CD to choosen folder
:: Use /D flag in case of different drive
CD /D %folder%

echo Installing projpicker.pyt at !folder!

:: Get files with curl (available on existing windows installs) and install
:: pyt file
echo Retrieving toolbox from:
echo - !PYTURL!
curl.exe -s --output projpicker.pyt --url !PYTURL!

:: Latest git
echo Retrieving module from:
echo - !GITURL!
curl.exe -s -OL !GITURL!

:: Extract root
tar -xf main.zip

:: Move module to main folder
move projpicker-main\projpicker projpicker >nul
:: Move bootstrap pyproj into projpicker root
move projpicker-main\guis\arcgispro\pyproj projpicker\pyproj >nul

:: clean up
Rmdir /Q /S "projpicker-main"
del /f /q "main.zip"

echo Finished.
endlocal
