
# AGENTS.md - SIGMA-RS (Sistema de Gestión de Tickets para Material Rodante)

> Instrucciones para agentes de codificación AI. Responde en **español**. Código, docstrings y documentación técnica en **inglés**.

## Referencia Rápida

```PowerShell
# 1. Clonar repositorio
git clone https://github.com/[usuario]/SIGMA-RS.git
cd SIGMA-RS

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno
venv\Scripts\activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Migraciones
python manage.py makemigrations
python manage.py migrate

# 6. Crear superusuario
python manage.py createsuperuser

# 7. Levantar servidor
python -m waitress --host=0.0.0.0 --port=8000 config.wsgi:application
```

## Estructura del Proyecto

```
sigma-rs/
├── config/           # Configuración Django (settings, wsgi, urls)
├── core/             # App principal (modelos, vistas, templates)
├── db/               # Base de datos SQLite
├── static/           # Archivos estáticos
├── docs/             # Documentación
├── manage.py         # Entrypoint Django
├── requirements.txt  # Dependencias
└── tests/            # Tests (estructura espejo)
```

## Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Backend | Django | 5.1 |
| Servidor WSGI | Waitress | 3.0.0 |
| Base de datos | SQLite | (default) |
| Static files | WhiteNoise | 6.7.0 |
| Python | 3.11+ | |
| Control de versiones | Git + GitHub | |

## Principios de Desarrollo

- **SOLID**: Aplica los principios SOLID en el diseño de clases y servicios.
- **TDD**: Desarrolla usando Test Driven Development (Red-Green-Refactor):
  1. Escribe primero el test (falla - rojo)
  2. Implementa el código mínimo para pasar el test (verde)
  3. Refactoriza manteniendo los tests en verde
- **Pequeños commits**: Usa mensajes convencionales (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`)
- **No subir archivos sensibles**: Nunca commitear `.env`, `db.sqlite3`, credenciales, ni archivos de base de datos.
- **Repositorio público**: No subir datos oficiales, personales ni confidenciales. Usar `.env` para configuración sensible y mantenerlo fuera del control de versiones.
- **CI/CD**: Validar siempre con `python manage.py check` y tests antes de mergear.

- **Documentación actualizada**: Actualiza la documentación cada vez que realices un cambio importante en el código o la arquitectura.
- **Changelog**: Mantén un archivo `docs/CHANGELOG.md` con los cambios relevantes de cada versión.
- **Control de versiones**: Usa git con tags semánticos (`v1.0.0`, `v1.1.0`, etc.) para marcar releases y facilitar el seguimiento de versiones.

## Glosario y Convenciones de Dominio

| Abreviatura | Significado |
|-------------|-------------|
| Loc, Locs | Locomotora(s) |
| CR, CCRR | Coche(s) Remolcado(s) |
| CM, CMN | Coche Motor |
| GOP | Guardia Operativa |
| OT | Orden de Trabajo |

### Jerarquía de Unidades de Mantenimiento

```
UnidadMantenimiento (abstracta)
├── Locomotora (Marca, Modelo, Activo)
├── CocheRemolcado (Marca, Clase, Activo)
└── CocheMotor (Marca, Modelo, CantidadCoches, Activo)
```

### Fabricantes

| Marca | Fabrica |
|-------|---------|
| CNR (Dalian) | Locomotoras, Coches Remolcados, Coches Motor |
| GM (General Motors) | Solo Locomotoras (en Argentina) |
| Materfer | Solo Coches Remolcados |

## Estilo de Código

- **Imports**: stdlib → terceros → locales
- **Type hints** obligatorios en funciones públicas
- **Docstrings**: Formato Google, en inglés. Tests con docstrings en español (contexto de negocio)
- **Nombres**: Clases en PascalCase, funciones en snake_case, constantes en UPPER_SNAKE
- **Modelos Django**: Sufijo `Model`, `verbose_name` en español, UUIDField como PK, timestamps automáticos
- **Tests**: Estructura espejo, clases `Test*`, fixtures en `conftest.py`, mocks con `unittest.mock.patch`

## Ejemplo de Modelo Django

```python
import uuid
from django.db import models

class TicketModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField("Título", max_length=200)
    descripcion = models.TextField("Descripción")
    estado = models.CharField("Estado", max_length=20)
    created_at = models.DateTimeField("Creado", auto_now_add=True)

    class Meta:
        db_table = "ticket"
        verbose_name = "Ticket"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.titulo
```

## Ejemplo de Test

```python
import pytest
from core.models import TicketModel

class TestTicketModel:
    """Pruebas de negocio para el modelo Ticket."""

    def test_str(self):
        ticket = TicketModel(titulo="Test", descripcion="Desc", estado="nuevo")
        assert str(ticket) == "Test"
```

## Manejo de Errores y Logging

- Usa excepciones descriptivas (`ValueError`, custom exceptions)
- Logging con `logging.getLogger(__name__)`
- Cierra conexiones en bloques `finally`

## Flujo de Trabajo con Git

```powershell
# Hacer cambios
git add .
git commit -m "feat: descripción clara"
git push origin main

# En el servidor
# En el servidor corre el script servidor_auto.ps1, que chequea cambios, realiza pull y reinicia waitress
git pull origin main
# Reiniciar waitress si es necesario
```

## Entorno y Configuración

- **ALLOWED_HOSTS**: `['*']` o IPs específicas
- **Base de datos**: SQLite por defecto, migrar a PostgreSQL si hay problemas de concurrencia
- **Proxy corporativo**: Configurar pip y git según documentación

## CI Pipeline

Ejecutar en cada push/PR:

```powershell
python manage.py check
python manage.py makemigrations --check
pytest -q
```

---

Para detalles adicionales, ver `docs/SIGMA-RS_RESUMEN_PROYECTO.md`.
El changelog se encuentra en `docs/CHANGELOG.md`.
