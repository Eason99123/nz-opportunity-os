@echo off
cd /d "%~dp0"

echo Starting local server...
echo.
echo Open:
echo http://127.0.0.1:8000/web/index.html
echo.

python -m http.server 8000

pause