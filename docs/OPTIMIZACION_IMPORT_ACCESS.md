# Contexto: Optimización Importación Access Legacy

## Problema

Importar ~725,000 registros de kilometrajes desde `baseLocs.mdb` (Access 2.0) tarda demasiado tiempo.

## Flujo Actual (rama `dev`)

```
Access .mdb (ODBC/COM)
      ↓
extractor_access.ps1 (PowerShell 32-bit)
      ↓
JSON por stdout
      ↓
access_extractor.py → access_kilometrage_importer.py
      ↓
SQLite (Django ORM)
```

## Cuellos de Botella Identificados

| # | Problema | Impacto | Archivo |
|---|----------|---------|---------|
| 1 | `$results += ...` en PowerShell | **CRÍTICO** - O(n²) | `extractor_access.ps1` |
| 2 | Sin paginación en query SQL | **ALTO** | `extractor_access.ps1` |
| 3 | `stdout.read()` bloquea | **MEDIO** | `access_extractor.py` |
| 4 | Cada `bulk_create` es transacción separada | **MEDIO** | `access_kilometrage_importer.py` |
| 5 | Índices activos durante inserción | **MEDIO** | SQLite |

## Optimizaciones a Implementar

### 1. PowerShell - ArrayList (PRIORIDAD MÁXIMA)

```powershell
# ANTES (O(n²) - muy lento)
$results = @()
while (-not $rs.EOF) {
    $results += [PSCustomObject]@{ ... }
}

# DESPUÉS (O(n) - rápido)
$results = [System.Collections.Generic.List[PSCustomObject]]::new()
while (-not $rs.EOF) {
    $results.Add([PSCustomObject]@{ ... })
}
```

### 2. Python - Transacción Única

```python
from django.db import transaction

with transaction.atomic():
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i+BATCH_SIZE]
        KilometrageRecordModel.objects.bulk_create(batch, ignore_conflicts=True)
```

### 3. PRAGMAs SQLite

```python
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("PRAGMA synchronous = OFF")
    cursor.execute("PRAGMA journal_mode = MEMORY")
    cursor.execute("PRAGMA cache_size = -64000")
    # ... importar ...
    cursor.execute("PRAGMA synchronous = FULL")
```

### 4. Paginación SQL (opcional)

```powershell
$pageSize = 50000
$query = "SELECT TOP $pageSize * FROM Kilometraje WHERE ID > $lastId ORDER BY ID"
```

## Archivos a Modificar (rama dev)

- `extractor_access.ps1` - ArrayList, paginación
- `apps/tickets/infrastructure/services/access_kilometrage_importer.py` - Transacción atómica, PRAGMAs
- `apps/tickets/infrastructure/services/access_extractor.py` - Streaming JSON (opcional)

## Estimación de Mejora

| Optimización | Speedup |
|--------------|---------|
| ArrayList PowerShell | 70-80% más rápido |
| Transacción única | 20-30% más rápido |
| PRAGMAs SQLite | 30-50% más rápido |
| **Combinado** | **~10x más rápido** |

De 30-60+ minutos → 2-5 minutos estimado.

## Comando para Empezar

```bash
git checkout dev
# Luego implementar optimizaciones
```
