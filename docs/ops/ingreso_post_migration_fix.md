# Remediacion post-migracion de ingreso por email

Este documento describe dos scripts para corregir configuracion de ingreso email luego de una migracion.

## 1) Servidor

- Script PowerShell: `ops/fix_ingreso_server.ps1`
- Launcher simple: `ops/fix_ingreso_server.bat`

### Que corrige

- Verifica que se ejecute dentro del repo (presencia de `manage.py`).
- Crea `.env` si no existe.
- Asegura claves `INGRESO_TRAY_TOKEN` y `INGRESO_EMAIL_SIGNING_SECRET` en `.env`.
- Si faltan valores, los pide por consola y actualiza el archivo de forma segura.
- Ejecuta validacion de runtime con `python manage.py shell -c ...`.
- Puede probar endpoint `/sigma/api/tray/online/` con token (opcional).

### Uso recomendado

```powershell
pwsh -File .\ops\fix_ingreso_server.ps1
```

O para usuarios no tecnicos:

```bat
ops\fix_ingreso_server.bat
```

Opciones utiles:

- `-SkipOnlineCheck`: omite chequeo HTTP.
- `-ServerBaseUrl "http://HOST:8000/sigma"`: define URL para chequeo online.
- `-NonInteractive`: falla si faltan valores (sin prompts).

## 2) Terminales

- Script PowerShell: `install/tray/fix_ingreso_terminal.ps1`
- Launcher simple: `install/tray/fix_ingreso_terminal.bat`

### Que corrige

- Crea/valida `%APPDATA%\SigmaRS\tray-config.json`.
- Asegura `sigma_base_url`, `ingreso_tray_token`, `poll_interval_seconds`.
- Si faltan, pide valores por consola.
- Reescribe launcher de inicio automatico en carpeta Startup.
- Intenta iniciar `SigmaRSIngresoTray.exe` si existe.
- Muestra resumen PASS/FAIL y datos para enviar al administrador.

### Uso recomendado

```powershell
pwsh -File .\install\tray\fix_ingreso_terminal.ps1
```

Para usuarios no tecnicos:

```bat
install\tray\fix_ingreso_terminal.bat
```

Opciones utiles:

- `-TrayExePath "C:\SigmaRS\SigmaRSIngresoTray.exe"`: ruta custom del ejecutable.
- `-NonInteractive`: falla si faltan valores y no puede preguntar.

## Seguridad y notas operativas

- Los scripts no muestran secretos completos en consola; usan formato enmascarado.
- Son idempotentes: se pueden ejecutar varias veces sin romper configuracion.
- `INGRESO_EMAIL_SIGNING_SECRET` solo se configura en servidor (no en terminal).
- Mantener token/secret fuera de mails y chats abiertos.

## Entradas requeridas

- Servidor:
  - `INGRESO_TRAY_TOKEN`
  - `INGRESO_EMAIL_SIGNING_SECRET`
- Terminal:
  - `sigma_base_url` (ej. `http://SERVER:8000/sigma`)
  - `ingreso_tray_token` (debe coincidir con servidor)
  - `poll_interval_seconds` (recomendado 15)

## Troubleshooting rapido

- Si el script servidor falla en `manage.py shell`, activar entorno Python correcto y reintentar.
- Si terminal no inicia tray, verificar que exista `SigmaRSIngresoTray.exe` y permisos de usuario.
- Si endpoint online falla, verificar URL base, servicio activo y token.
