@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0fix_ingreso_terminal.ps1" %*
exit /b %errorlevel%
