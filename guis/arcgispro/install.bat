:: fchooser.bat
:: launches a folder chooser and outputs choice to the console
:: https://stackoverflow.com/a/15885133/1683264

@echo off
setlocal

set "psCommand="(new-object -COM 'Shell.Application')^
.BrowseForFolder(0,'Please choose a folder.',0,0).self.path""

for /f "usebackq delims=" %%I in (`powershell %psCommand%`) do set "folder=%%I"

setlocal enabledelayedexpansion
:: Exit if cancel
IF [!folder!] == [] exit 0
echo You chose !folder!

:: Install

curl.exe --output !folder!\projpicker.pyt --url https://raw.githubusercontent.com/HuidaeCho/projpicker/main/guis/arcgispro/projpicker.pyt

curl.exe -OL --output !folder! --url https://github.com/HuidaeCho/projpicker/archive/main.zip

tar -xf !folder!/main.zip

move !folder!/projpicker-main/projpicker !folder!/projpicker

:: clean up
Rmdir /Q /S "!folder!/projpicker-main"
echo !folder!\main.zip
del /f /q "!folder!\main.zip"

endlocal
