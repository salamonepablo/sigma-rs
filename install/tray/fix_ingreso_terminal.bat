@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0fix_ingreso_terminal.ps1" -PackagePath "%~dp0terminal-fix-config.json" -NonInteractive %*
exit /b %errorlevel%
