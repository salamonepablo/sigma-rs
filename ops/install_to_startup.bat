@echo off
REM install_to_startup.bat - Copy ops\start_sigma_rs.bat into the current user's Startup folder
REM Run this script from the project folder or double-click it. It will copy
REM `ops\start_sigma_rs.bat` into the user's Startup folder so it runs on login.

set "PROJECT=C:\Users\pablo.salamone\Programmes\sigma-rs"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

if not exist "%PROJECT%\ops\start_sigma_rs.bat" (
  echo File not found: %PROJECT%\ops\start_sigma_rs.bat
  exit /b 1
)

echo Copying start script to Startup folder...
copy /Y "%PROJECT%\ops\start_sigma_rs.bat" "%STARTUP%\start_sigma_rs.bat" >nul
if %errorlevel% neq 0 (
  echo Failed to copy to %STARTUP%
  exit /b 1
)

echo Installed to: %STARTUP%\start_sigma_rs.bat
exit /b 0
