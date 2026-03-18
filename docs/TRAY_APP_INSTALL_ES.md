# Sigma-RS Tray App - Instalacion (Outlook Draft)

## Objetivo

La tray app consulta Sigma-RS por envios de ingreso pendientes y abre un
borrador en Outlook en la PC local. El usuario hace clic en **Enviar**.

## Requisitos

- Windows con Outlook instalado y configurado.
- Acceso a la URL del servidor Sigma-RS.
- Valores de secretos compartidos por el administrador:
  - `INGRESO_TRAY_TOKEN`
  - `INGRESO_EMAIL_SIGNING_SECRET`

## Instalacion (recomendado)

1. Generar el ejecutable y el instalador (desde el repo):

```powershell
pip install pyinstaller
./tray-app/packaging/build.ps1 -OneFile
iscc tray-app/packaging/installer.iss
```

2. Copiar el instalador desde `tray-app/packaging/dist` a la PC destino.
3. Ejecutar el instalador y, si se desea, habilitar **Run on startup**.

## Configuracion

Crear o editar el archivo:

`%APPDATA%\SigmaRS\tray-config.json`

```json
{
  "sigma_base_url": "http://SERVER:8000/sigma",
  "ingreso_tray_token": "REEMPLAZAR_CON_TOKEN",
  "poll_interval_seconds": 15
}
```

Notas:
- `ingreso_tray_token` debe coincidir con `INGRESO_TRAY_TOKEN` del servidor.
- `INGRESO_EMAIL_SIGNING_SECRET` se valida del lado servidor; no es necesario
  colocarlo en el config local.

Overrides opcionales via variables de entorno:

- `SIGMA_BASE_URL`
- `INGRESO_TRAY_TOKEN`
- `POLL_INTERVAL_SECONDS`
- `TRAY_CONFIG_PATH`

## Ejecutar (manual)

```powershell
SigmaRSIngresoTray.exe
```

## Verificacion

1. Crear un ingreso en Sigma-RS.
2. Outlook debe abrir un borrador con el PDF adjunto.
3. El usuario hace clic en **Enviar**.
4. El servidor marca el envio como **drafted** (o **failed** si hubo error).

## Troubleshooting

- Si no se abre el borrador:
  - Verificar que la tray app este ejecutandose.
  - Verificar que `sigma_base_url` sea accesible.
  - Verificar que `ingreso_tray_token` coincida con el servidor.
- Si fallan los llamados a la API, revisar la consola de la tray app.
