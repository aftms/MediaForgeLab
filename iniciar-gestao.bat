@echo off
cd /d "%~dp0"
call "%~dp0run-python.bat" "%~dp0control.py" manage
echo Gestao local: http://127.0.0.1:8092/
pause
