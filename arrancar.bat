@echo off
chcp 65001 >nul
echo ============================================
echo   Material Rodante - Prototipo
echo ============================================

call venv\Scripts\activate.bat

:: Obtener IP local para mostrar
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP: =%

echo.
echo   Servidor iniciando en:
echo   - Local:  http://localhost:8000
echo   - Red:    http://%IP%:8000
echo.
echo   Compartir la URL de "Red" con los compañeros.
echo   Para detener: Ctrl+C
echo ============================================
echo.

:: Waitress sirve Django en 0.0.0.0:8000 (todas las interfaces de red)
python -m waitress --host=0.0.0.0 --port=8000 config.wsgi:application
