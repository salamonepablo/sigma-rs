; Sigma-RS Tray App installer (Inno Setup)

[Setup]
AppName=Sigma-RS Tray App
AppVersion=1.0.0
DefaultDirName={pf}\SigmaRS\TrayApp
DefaultGroupName=Sigma-RS
OutputDir=tray-app\packaging\dist
OutputBaseFilename=SigmaRS-TrayApp-Setup
Compression=lzma
SolidCompression=yes

[Tasks]
Name: "startup"; Description: "Run tray app on Windows startup"; Flags: unchecked

[Files]
Source: "dist\SigmaRSIngresoTray.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "tray-app\config\tray-config.example.json"; DestDir: "{userappdata}\SigmaRS"; DestName: "tray-config.json"; Flags: onlyifdoesntexist

[Icons]
Name: "{group}\Sigma-RS Tray App"; Filename: "{app}\SigmaRSIngresoTray.exe"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "SigmaRSTrayApp"; ValueData: "{app}\SigmaRSIngresoTray.exe"; Tasks: startup

[Run]
Filename: "{app}\SigmaRSIngresoTray.exe"; Description: "Run Sigma-RS Tray App"; Flags: nowait postinstall skipifsilent
