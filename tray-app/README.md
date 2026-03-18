# Sigma-RS Tray App (Ingreso Email)

This tray app polls Sigma-RS for pending ingreso email dispatches and sends them
using the local Outlook profile on the Windows PC.

## Requirements

- Windows with Outlook installed and configured
- Python 3.11+
- pywin32
- requests

## Configuration

Set the following environment variables:

- `SIGMA_BASE_URL` (e.g. `http://localhost:8000/sigma`)
- `INGRESO_TRAY_TOKEN` (must match server `INGRESO_TRAY_TOKEN`)
- `POLL_INTERVAL_SECONDS` (optional, default 15)

## Run

```bash
python tray-app/src/poller.py
```

The poller will:

1. Fetch pending ingreso payloads.
2. Download the PDF attachment.
3. Send the email via Outlook COM.
4. Post the result back to the server.
