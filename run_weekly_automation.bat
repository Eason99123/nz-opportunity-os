@echo off
cd /d "%~dp0"

powershell.exe ^
    -NoProfile ^
    -ExecutionPolicy Bypass ^
    -File ".\automation\run_weekly_automation.ps1"

pause