# Sigma-RS Tray App (Ingreso Email)

This tray app polls Sigma-RS for pending ingreso email dispatches and sends them
using the local Outlook profile on the Windows PC.

## Requirements

- Windows with Outlook installed and configured
- Python 3.11+
- pywin32
- requests

## Configuration

Preferred: create `%APPDATA%\SigmaRS\tray-config.json`:

```json
{
  "sigma_base_url": "http://localhost:8000/sigma",
  "ingreso_tray_token": "YOUR_TOKEN",
  "poll_interval_seconds": 15
}
```

Optional overrides via environment variables:

- `SIGMA_BASE_URL`
- `INGRESO_TRAY_TOKEN`
- `POLL_INTERVAL_SECONDS`
- `TRAY_CONFIG_PATH` (custom path to tray-config.json)

## Run

```bash
python tray-app/src/poller.py
```

## Packaging

Install PyInstaller:

```bash
pip install pyinstaller
```

Build executable:

```powershell
./tray-app/packaging/build.ps1 -OneFile
```

Create installer (requires Inno Setup):

```powershell
iscc tray-app/packaging/installer.iss
```

The poller will:

1. Fetch pending ingreso payloads.
2. Download the PDF attachment.
3. Open an Outlook draft (user clicks Send).
4. Post the result back to the server.
