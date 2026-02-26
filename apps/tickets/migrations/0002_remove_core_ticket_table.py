"""Migration to remove the legacy core_ticket table from prototype."""

from django.db import migrations


class Migration(migrations.Migration):
    """Remove the core_ticket table left over from the prototype."""

    dependencies = [
        ("tickets", "0001_initial_models"),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS core_ticket;",
            reverse_sql="""
                CREATE TABLE IF NOT EXISTS core_ticket (
                    numero INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATETIME NOT NULL,
                    titulo VARCHAR(200) NOT NULL,
                    descripcion TEXT NOT NULL,
                    estado VARCHAR(20) NOT NULL,
                    prioridad VARCHAR(10) NOT NULL,
                    creado_por_id INTEGER NOT NULL REFERENCES auth_user(id),
                    actualizado DATETIME NOT NULL
                );
            """,
        ),
    ]
