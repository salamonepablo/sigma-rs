@echo off
chcp 65001 >nul
echo ============================================
echo   SETUP - Prototipo Material Rodante
echo ============================================
echo.

:: Crear entorno virtual
echo [1/4] Creando entorno virtual...
python -m venv venv
if errorlevel 1 (
    echo ERROR: No se pudo crear el entorno virtual.
    echo Verificar que Python este instalado y en el PATH.
    pause
    exit /b 1
)

:: Activar e instalar dependencias
echo [2/4] Instalando dependencias...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

:: Migrar base de datos
echo [3/4] Creando base de datos...
python manage.py migrate --run-syncdb

:: Crear superusuario
echo [4/4] Crear usuario administrador:
echo.
python manage.py createsuperuser

echo.
echo ============================================
echo   SETUP COMPLETO
echo   Ejecutar 'start.bat' para iniciar
echo ============================================
pause
