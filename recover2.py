import sqlite3
import sys

src = sqlite3.connect("db/app.db")
dst = sqlite3.connect("db/app_recovered.sqlite3")
src.row_factory = sqlite3.Row

schema_rows = src.execute(
    "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND type IN ('table','index')"
).fetchall()
for row in schema_rows:
    try:
        dst.execute(row[0])
    except Exception as e:
        print(f"Schema SKIP: {e}", file=sys.stderr, flush=True)

tables = src.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for (table,) in tables:
    print(f"Copiando {table}...", flush=True)
    try:
        rows = src.execute(f'SELECT * FROM "{table}"').fetchall()
        for row in rows:
            try:
                placeholders = ",".join(["?"] * len(row))
                dst.execute(
                    f'INSERT OR IGNORE INTO "{table}" VALUES ({placeholders})',
                    tuple(row),
                )
            except Exception as e:
                print(f"  Fila SKIP en {table}: {e}", file=sys.stderr, flush=True)
        dst.commit()
        print(f"  OK ({len(rows)} filas)", flush=True)
    except Exception as e:
        print(f"  Tabla SKIP {table}: {e}", file=sys.stderr, flush=True)

src.close()
dst.close()
print("Listo.")
