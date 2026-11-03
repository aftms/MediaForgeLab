@echo off
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
  "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" %*
) else (
  py -3 %*
)
exit /b %errorlevel%
