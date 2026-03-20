Instalador SigmaRS Ingreso Tray (pendrive)

Archivos a copiar al pendrive o carpeta temporal:
- SigmaRSIngresoTray.exe
- install_tray.ps1
- tray-token.txt (una sola linea con el token)
- server-ip.txt (una sola linea con la IP/host del servidor)
- server-port.txt (una sola linea con el puerto, ej 8000)
- server-scheme.txt (una sola linea con http o https)

Ejecutar en la PC cliente:
1) Abrir PowerShell
2) Ir a la carpeta del pendrive
3) Ejecutar:
   powershell -ExecutionPolicy Bypass -File .\install_tray.ps1

Que hace el instalador:
- Copia el exe a C:\SigmaRS\SigmaRSIngresoTray.exe
- Crea el .bat en Inicio de Windows para ejecutar el tray al loguear
- Crea %APPDATA%\SigmaRS\tray-config.json

Notas:
- Si cambia IP/host, editar server-ip.txt y volver a correr el instalador.
- Si cambia puerto, editar server-port.txt y volver a correr el instalador.
- Si cambia esquema (http/https), editar server-scheme.txt y volver a correr el instalador.
- Si cambia token, editar tray-token.txt y volver a correr el instalador.
