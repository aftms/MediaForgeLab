@echo off
cd /d "%~dp0"
call "%~dp0run-python.bat" "%~dp0control.py" start
pause
