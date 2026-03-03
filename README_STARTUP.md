# Startup installation for SIGMA-RS automatic server

Instrucciones rápidas (español):

- To install: run `install_to_startup.bat` (it copies `start_sigma_rs.bat` to your Startup folder).
- To run manually: execute `start_sigma_rs.bat` in the project root.
- To remove from Startup: delete `start_sigma_rs.bat` from `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`.

Commands (PowerShell as admin if needed):

```powershell
cd 'C:\Users\pablo.salamone\Programmes\sigma-rs'
Start-Process -FilePath .\install_to_startup.bat -Verb RunAs
```

Notes:

- The batch uses an absolute project path: `C:\Users\pablo.salamone\Programmes\sigma-rs`.
- The installed startup file will launch `servidor_auto.ps1` in a minimized PowerShell window.
- If you prefer a different Startup target (all-users), copy the file to `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup` instead.
