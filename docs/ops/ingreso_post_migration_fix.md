# Remediacion post-migracion de ingreso por email

Flujo simplificado para que usuarios no tecnicos no tengan que escribir token/secret manualmente.

## 1) Operador SERVIDOR

Archivos:
- `ops/fix_ingreso_server.ps1`
- `ops/fix_ingreso_server.bat`

Que hace:
- Verifica repo (`manage.py`) y crea/actualiza `.env`.
- Asegura y persiste claves canonicas: `INGRESO_TRAY_TOKEN`, `INGRESO_EMAIL_SIGNING_SECRET`, `SIGMA_BASE_URL`, `POLL_INTERVAL_SECONDS`.
- Genera paquete para terminales en `ops/out/ingreso_terminal_fix/`.
- Mantiene validaciones existentes (`manage.py shell` y chequeo online opcional).

Paso a paso:
1. En el servidor, ejecutar:
   ```bat
   ops\fix_ingreso_server.bat
   ```
2. Si faltan datos canonicos, el script los pide una sola vez y los guarda en `.env`.
3. Al finalizar, confirmar que el resumen quede en `PASS`.
4. Ir a carpeta `ops/out/ingreso_terminal_fix/` y copiar estos archivos para distribuir:
   - `terminal-fix-config.json`
   - `LEEME_TERMINAL.txt`

Opcional no interactivo (si ya sabe todos los valores):
```powershell
pwsh -File .\ops\fix_ingreso_server.ps1 -TerminalBaseUrl "http://SERVER:8000/sigma" -TrayToken "TOKEN" -EmailSigningSecret "SECRET" -PollIntervalSeconds 15 -NonInteractive
```

## 2) Usuario TERMINAL

Archivos:
- `install/tray/fix_ingreso_terminal.ps1`
- `install/tray/fix_ingreso_terminal.bat`

Paso a paso:
1. Copiar `terminal-fix-config.json` en la misma carpeta de `fix_ingreso_terminal.bat`.
2. Ejecutar:
   ```bat
   fix_ingreso_terminal.bat
   ```
3. El script hace todo automatico (sin pedir token/secret):
   - sobrescribe `%APPDATA%\SigmaRS\tray-config.json` con valores canonicos,
   - asegura launcher en Startup,
   - intenta iniciar `SigmaRSIngresoTray.exe`.
4. Si falta el paquete, falla con mensaje accionable indicando copiar `terminal-fix-config.json`.

## 3) Evidencia que deben enviar

- Captura del bloque `==== Resumen ====` del script terminal.
- Debe verse todo `PASS`.
- Incluir ruta mostrada del launcher (`SigmaRSIngresoTray.bat`).

## Notas operativas

- Comportamiento idempotente: se puede ejecutar varias veces.
- `INGRESO_EMAIL_SIGNING_SECRET` solo vive en servidor.
- En este entorno controlado se permite incluir token completo en el paquete distribuible.
