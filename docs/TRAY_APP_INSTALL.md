# Sigma-RS Tray App نصب / Installation (Outlook Draft)

## Purpose

This tray app polls Sigma-RS for pending ingreso email dispatches and opens an
Outlook draft on the local Windows PC. The user clicks **Send** manually.

## Prerequisites

- Windows PC with Outlook installed and configured.
- Access to the Sigma-RS server URL.
- Shared secret values from the server administrator:
  - `INGRESO_TRAY_TOKEN`
  - `INGRESO_EMAIL_SIGNING_SECRET`

## Install (recommended)

1. Build the executable and installer (from the repo):

```powershell
pip install pyinstaller
./tray-app/packaging/build.ps1 -OneFile
iscc tray-app/packaging/installer.iss
```

2. Copy the installer from `tray-app/packaging/dist` to the target PC.
3. Run the installer and optionally enable **Run on startup**.

## Configure

Create or edit the config file:

`%APPDATA%\SigmaRS\tray-config.json`

```json
{
  "sigma_base_url": "http://SERVER:8000/sigma",
  "ingreso_tray_token": "REPLACE_WITH_TOKEN",
  "poll_interval_seconds": 15
}
```

Notes:
- `ingreso_tray_token` must match the server `INGRESO_TRAY_TOKEN`.
- `INGRESO_EMAIL_SIGNING_SECRET` is validated server-side; no need to place it
  in the tray config.

Optional overrides via environment variables:

- `SIGMA_BASE_URL`
- `INGRESO_TRAY_TOKEN`
- `POLL_INTERVAL_SECONDS`
- `TRAY_CONFIG_PATH`

## Run (manual)

```powershell
SigmaRSIngresoTray.exe
```

## Verify

1. Create an ingreso in Sigma-RS.
2. Outlook should open a draft with the PDF attached.
3. User clicks **Send**.
4. The server marks the dispatch as **drafted** (or **failed** if error).

## Troubleshooting

- If no draft opens, check:
  - Tray app is running.
  - `sigma_base_url` is reachable.
  - `ingreso_tray_token` matches the server.
- If API calls fail, inspect the tray app console output.
