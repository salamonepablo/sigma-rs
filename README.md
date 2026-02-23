# Prototipo Material Rodante - Línea Roca

Prueba de concepto para validar arquitectura web como reemplazo de Microsoft Access.

## Requisitos

- Python 3.11+ instalado y en el PATH
- Conexión a internet (solo para el primer setup, descarga dependencias)

## Instalación (una sola vez)

1. Abrir una terminal (CMD o PowerShell) en esta carpeta
2. Ejecutar:

```
setup.bat
```

3. Va a pedir crear un usuario administrador (nombre, email, contraseña)

## Iniciar el servidor

```
start.bat
```

Va a mostrar la IP local, por ejemplo:
```
Red: http://192.168.1.50:8000
```

Compartir esa URL con los compañeros.

## Crear usuarios de prueba

Con el servidor detenido, ejecutar:

```
venv\Scripts\activate
python crear_usuarios_prueba.py
```

Esto crea 4 usuarios (operativo1, operativo2, manten1, manten2) con password `test1234`.

## Prueba de acceso por red

1. Desde tu PC: abrir `http://localhost:8000`
2. Desde otra PC de la red: abrir `http://<TU-IP>:8000`
3. Si no accede, verificar que el firewall permita el puerto 8000 (ver abajo)

## Abrir puerto en Firewall de Windows (si es necesario)

Abrir PowerShell **como administrador** y ejecutar:

```powershell
New-NetFirewallRule -DisplayName "Proto MR - Puerto 8000" -Direction Inbound -Port 8000 -Protocol TCP -Action Allow
```

## Estructura

```
proto_mr/
├── config/          ← Configuración Django
├── core/            ← App principal (tickets CRUD)
├── db/              ← Base de datos SQLite (se crea sola)
├── setup.bat        ← Instalación inicial
├── start.bat        ← Arrancar servidor
└── crear_usuarios_prueba.py
```
