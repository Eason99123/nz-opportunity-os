@echo off
setlocal

cd /d "%~dp0"

echo ============================================
echo NZ Student Opportunity OS
echo Demo Mode
echo ============================================
echo.

echo Preparing safe demo data...
echo.

python ".\src\setup_demo.py"

if errorlevel 1 (
    echo.
    echo Demo setup failed.
    echo Please review the output above.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo Demo environment ready.
echo ============================================
echo.
echo Dashboard:
echo http://127.0.0.1:8000/web/index.html
echo.
echo Press Ctrl+C to stop the local server.
echo.

start "" "http://127.0.0.1:8000/web/index.html"

python -m http.server 8000

endlocal