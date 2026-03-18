# build.ps1 - Build tray app executable with PyInstaller

param(
    [switch]$OneFile
)

$projectPath = "C:\Users\pablo.salamone\Programmes\sigma-rs"
Set-Location $projectPath

$entry = "tray-app/src/poller.py"
$name = "SigmaRSIngresoTray"
$data = "tray-app/config/tray-config.example.json;tray-config"

if ($OneFile) {
    pyinstaller --onefile --name $name --add-data $data $entry
}
else {
    pyinstaller --name $name --add-data $data $entry
}
