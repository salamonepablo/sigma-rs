# SIGMA-RS - Resumen del Proyecto

## Descripción General
Sistema de gestión de tickets para Material Rodante, desarrollado en Django. Permite a múltiples usuarios crear, gestionar y dar seguimiento a tickets desde distintas PCs en la red corporativa.

---

## Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Backend | Django | 5.1 |
| Servidor WSGI | Waitress | 3.0.0 |
| Base de datos | SQLite | (default) |
| Static files | WhiteNoise | 6.7.0 |
| Python | 3.11+ | |
| Control de versiones | Git + GitHub | |

---

## Arquitectura Actual

```
[PC Usuarios (57 potenciales)]
        |
        | HTTP :8000
        v
[PC Servidor - Windows]
    - Waitress (WSGI)
    - Django
    - SQLite (db.sqlite3)
    - Código en C:\users\pablo.salamone\Programmes\sigma-rs
```

---

## Repositorio GitHub

- **Nombre:** SIGMA-RS
- **Estructura del proyecto:**
```
sigma-rs/
├── config/           # Configuración Django (settings, wsgi, urls)
├── core/             # App principal (modelos, vistas, templates)
├── db/               # Base de datos SQLite
├── static/           # Archivos estáticos
├── .gitignore
├── arrancar.bat      # Script para levantar servidor (no funciona por políticas)
├── crear_usuarios_prueba.py
├── instalar.bat      # Script de instalación (no funciona por políticas)
├── manage.py
├── README.md
└── requirements.txt
```

---

## Configuración del Proxy Corporativo

La red corporativa requiere autenticación de proxy para acceso a internet.

### Para pip (`%APPDATA%\pip\pip.ini`):
```ini
[global]
proxy = http://USUARIO:PASSWORD@172.22.10.121:80
trusted-host = pypi.org
    pypi.python.org
    files.pythonhosted.org
```

### Para Git:
```bash
git config --global http.proxy http://USUARIO:PASSWORD@172.22.10.121:80
git config --global https.proxy http://USUARIO:PASSWORD@172.22.10.121:80
```

---

## Comandos de Instalación (paso a paso)

Los archivos .bat están bloqueados por políticas de IT. Usar PowerShell directamente:

```powershell
# 1. Clonar repositorio
git clone https://github.com/[usuario]/SIGMA-RS.git
cd SIGMA-RS

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno
venv\Scripts\activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Crear/aplicar migraciones
python manage.py makemigrations
python manage.py migrate

# 6. Crear superusuario
python manage.py createsuperuser

# 7. Levantar servidor
python -m waitress --host=0.0.0.0 --port=8000 config.wsgi:application
```

---

## Configuraciones Importantes en settings.py

### ALLOWED_HOSTS
```python
ALLOWED_HOSTS = ['*']  # O especificar IPs: ['localhost', '127.0.0.1', '172.22.181.1']
```

### Base de datos actual (SQLite)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### Migración futura a PostgreSQL (si es necesario)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sigma_rs',
        'USER': 'usuario',
        'PASSWORD': 'password',
        'HOST': 'servidor-postgres.empresa.com',
        'PORT': '5432',
    }
}
# Agregar a requirements.txt: psycopg2-binary==2.9.9
```

---

## Accesos y URLs

| Recurso | URL |
|---------|-----|
| Aplicación | http://[IP_SERVIDOR]:8000 |
| Admin Django | http://[IP_SERVIDOR]:8000/admin |
| Local dev | http://127.0.0.1:8000 |

---

## Flujo de Trabajo con Git

### Desarrollo local:
```powershell
# Hacer cambios en el código
git add .
git commit -m "Descripción del cambio"
git push origin main
```

### En el servidor (actualizar):
```powershell
cd C:\users\pablo.salamone\Programmes\sigma-rs
git pull origin main
# Reiniciar waitress si es necesario
```

---

## Gestión de Usuarios

### Crear usuario normal (no admin):
```python
# Desde Django shell
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.create_user('nombre_usuario', 'email@ejemplo.com', 'contraseña123')
```

### O desde Django Admin:
- Ir a /admin → Usuarios → Añadir usuario
- NO marcar "Superusuario" ni "Staff" para usuarios normales

---

## Limitaciones Conocidas

1. **SQLite**: Puede tener problemas con muchas escrituras concurrentes. Monitorear errores "database locked".

2. **Políticas IT**: 
   - No permite ejecutar archivos .bat
   - No permite instalar OpenSSH
   - No permite compartir carpetas
   - No permite conexión RDP entre PCs
   - No permite crear venv en unidades de red (G:\)

3. **Proxy**: Requiere autenticación para cualquier conexión a internet

4. **DB Browser for SQLite**: Bloquea la BD mientras está abierto. Cerrar antes de hacer cambios desde Django.

---

## Dependencias (requirements.txt)

```
django==5.1
waitress==3.0.0
whitenoise==6.7.0
```

---

## Funcionalidades Actuales

- [x] Sistema de login/logout
- [x] Gestión de tickets (CRUD)
- [x] Panel de administración Django
- [x] Multi-usuario desde red local
- [x] Filtrado de tickets por estado

---

## Próximos Pasos Sugeridos

1. Monitorear rendimiento con múltiples usuarios
2. Migrar a PostgreSQL si hay problemas de concurrencia
3. Implementar sync automático con GitHub en el servidor
4. Desarrollar funcionalidades adicionales según requerimientos

---

## Notas Adicionales

- El servidor actual está en IP: 172.22.181.1
- Capacidad estimada: 57 usuarios (42 PCs operativas + 15 oficinas)
- Para mejor rendimiento con Waitress: `--threads=16`

```powershell
python -m waitress --host=0.0.0.0 --port=8000 --threads=16 config.wsgi:application
```
