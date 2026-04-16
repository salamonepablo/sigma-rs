# Handoff: Reimport de kilometraje CCRR

## Contexto

Los registros de kilometraje de coches remolcados (CCRR) subidos previamente
tienen datos incorrectos. Hay que sobrescribirlos con el flag `--update`.

## Prerequisito: rutas de los .mdb

Los archivos Access están en la unidad G: (share de red). Verificá que estén
accesibles desde la notebook. Si la letra de unidad es distinta, ajustá
`--db-path` y `ACCESS_DB_PASSWORD` en el `.env`.

Ruta esperada: `G:\Material Rodante\IFM\DOCUMENT\baseCCRR.mdb`

## Comando a correr

Desde la raíz del repo, con el virtualenv activado:

```bash
python manage.py import_kilometrage_access \
  --unit-field Coche \
  --db-path "G:\Material Rodante\IFM\DOCUMENT\baseCCRR.mdb" \
  --db-password theidol-1995 \
  --update
```

- `--unit-field Coche` → indica que es CCRR (cualquier valor distinto a "Locs"
  activa el source `access_ccrr`)
- `--update` → usa `update_or_create` para sobrescribir registros existentes
- Al finalizar el comando recalcula automáticamente los snapshots de km para
  las unidades afectadas

## Dry-run opcional (revisar sin escribir)

```bash
python manage.py import_kilometrage_access \
  --unit-field Coche \
  --db-path "G:\Material Rodante\IFM\DOCUMENT\baseCCRR.mdb" \
  --db-password theidol-1995 \
  --dry-run
```

## Si querés importar desde una fecha específica

```bash
python manage.py import_kilometrage_access \
  --unit-field Coche \
  --db-path "G:\Material Rodante\IFM\DOCUMENT\baseCCRR.mdb" \
  --db-password theidol-1995 \
  --since-date 2020-01-01 \
  --update
```

## Contexto adicional para Claude

- Este repo es un monolito Django (Clean Architecture).
- La tabla de kilometraje es `KilometrageRecordModel`; los snapshots están en
  `UnitMaintenanceSnapshotModel`.
- El comando vive en
  `apps/tickets/management/commands/import_kilometrage_access.py`.
- El `.env` en la raíz del proyecto tiene las variables de configuración.
- Git user: Pablo Salamone.
- Respondé siempre en español.
