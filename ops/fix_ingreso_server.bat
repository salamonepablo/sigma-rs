@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0fix_ingreso_server.ps1" %*
exit /b %errorlevel%
