@echo off
cd /d "%~dp0.."

python ".\src\prune_published_batch.py"

pause