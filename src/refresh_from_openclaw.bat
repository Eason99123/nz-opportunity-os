@echo off
setlocal

cd /d "%~dp0.."

if not exist logs mkdir logs

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HHmmss"') do set TIMESTAMP=%%i

set LOGFILE=logs\refresh_%TIMESTAMP%.log
set LATESTLOG=logs\latest_refresh_run.log

echo Running OpenClaw refresh pipeline...
echo Log file: %LOGFILE%
echo.

(
    echo ============================================
    echo OpenClaw Refresh Run
    echo Timestamp: %TIMESTAMP%
    echo Project Root: %CD%
    echo ============================================
    echo.

    python src\refresh_from_openclaw.py

    set PIPELINE_EXIT_CODE=%ERRORLEVEL%

    echo.
    echo ============================================
    echo Refresh finished.
    echo Exit code: %PIPELINE_EXIT_CODE%
    echo ============================================

    exit /b %PIPELINE_EXIT_CODE%

) > "%LOGFILE%" 2>&1

set FINAL_EXIT_CODE=%ERRORLEVEL%

copy /y "%LOGFILE%" "%LATESTLOG%" >nul

type "%LOGFILE%"

echo.

if not "%FINAL_EXIT_CODE%"=="0" (
    echo Refresh failed.
    echo Opening log file...
    start notepad "%LOGFILE%"
) else (
    echo Refresh finished successfully.
)

echo.
pause

exit /b %FINAL_EXIT_CODE%