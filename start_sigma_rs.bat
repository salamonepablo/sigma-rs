@echo off
REM start_sigma_rs.bat - Launch SIGMA-RS automatic server script
REM Place this file anywhere or run it directly. When launched it will start
REM the PowerShell script `servidor_auto.ps1` from the project directory.

set "PROJECT=C:\Users\pablo.salamone\Programmes\sigma-rs"

pushd "%PROJECT%" || (
  echo Project path not found: %PROJECT%
  exit /b 1
)

echo Starting SIGMA-RS automatic server (servidor_auto.ps1)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"%PROJECT%\servidor_auto.ps1\"' -WindowStyle Minimized"

popd
exit /b 0
