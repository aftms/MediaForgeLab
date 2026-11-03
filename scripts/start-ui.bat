@echo off
cd /d "%~dp0.."
call run-python.bat control.py start
if errorlevel 1 exit /b %errorlevel%
start "" "http://127.0.0.1:8091/web/"
