param(
    [string]$DbPath,
    [string]$Tabla,
    [string]$UnitField,
    [string]$SinceDate = "01/01/1900",
    [string]$ClaveBD = "",
    [int]$ProgressEvery = 500
)

$invariantCulture = [System.Globalization.CultureInfo]::InvariantCulture

function Format-DateValue {
    param([object]$Value)

    if ($null -eq $Value -or $Value -eq "") {
        return $null
    }

    try {
        return ([datetime]$Value).ToString("yyyy-MM-dd", $invariantCulture)
    } catch {
        return $null
    }
}

function Format-DecimalInvariant {
    param([object]$Value)

    if ($null -eq $Value -or $Value -eq "") {
        return $null
    }

    try {
        return ([decimal]$Value).ToString($invariantCulture)
    } catch {
        return $null
    }
}

if (-not $DbPath -or -not (Test-Path $DbPath)) {
    [Console]::Error.WriteLine("DbPath invalido o inexistente: $DbPath")
    exit 1
}
if (-not $Tabla) {
    [Console]::Error.WriteLine("Debe indicar la tabla a consultar.")
    exit 1
}
if (-not $UnitField) {
    [Console]::Error.WriteLine("Debe indicar el campo de unidad.")
    exit 1
}

# Cadenas de conexión: intentamos primero ACE (suele soportar 64-bit) y luego Jet (solo 32-bit)
$passwordSegment = ""
if ($ClaveBD) {
    $passwordSegment = "Jet OLEDB:Database Password=$ClaveBD;"
}
$connStringACE = "Provider=Microsoft.ACE.OLEDB.12.0;Data Source=$DbPath;$passwordSegment"
$connStringJet = "Provider=Microsoft.Jet.OLEDB.4.0;Data Source=$DbPath;$passwordSegment"

# Instanciar el objeto COM para base de datos (ADODB)
try {
    $conn = New-Object -ComObject ADODB.Connection
    try {
        $conn.Open($connStringACE)
        [Console]::Error.WriteLine("Conexion exitosa a $DbPath usando ACE OLEDB.")
    } catch {
        $conn.Open($connStringJet)
        [Console]::Error.WriteLine("Conexion exitosa a $DbPath usando Jet OLEDB.")
    }
} catch {
    [Console]::Error.WriteLine("Error al conectar a la base de datos.")
    [Console]::Error.WriteLine("Mensaje original: $($_.Exception.Message)")
    [Console]::Error.WriteLine("NOTA: Si el error dice que el proveedor no esta registrado, probablemente debas ejecutar este script en una consola de PowerShell de 32-bits (SysWOW64).")
    exit
}

# Armar la consulta filtrando por fecha para optimizar el proceso
# Nota: En Access las fechas en SQL se envuelven en formato #MM/DD/YYYY# o #YYYY-MM-DD#
$dateField = ""
$selectFields = ""
if ($Tabla -ieq "Kilometraje") {
    $dateField = "Fecha"
    $selectFields = "[$UnitField], [Fecha], [Kms_diario], [Observaciones]"
} else {
    $dateField = "Fecha_desde"
    $selectFields = "[$UnitField], [Fecha_desde], [Fecha_hasta], [Fecha_est], [Intervencion], [Lugar], [Observaciones]"
}

$query = "SELECT $selectFields FROM [$Tabla] WHERE [$dateField] > #$SinceDate#"
$countQuery = "SELECT COUNT(*) FROM [$Tabla] WHERE [$dateField] > #$SinceDate#"
$countRs = $conn.Execute($countQuery)
$totalRows = 0
if ($countRs -and -not $countRs.EOF) {
    $totalRows = [int]$countRs.Fields.Item(0).Value
}
$rs = New-Object -ComObject ADODB.Recordset
$rs.CursorLocation = 3
$rs.Open($query, $conn, 3, 1)

$progressEvery = $ProgressEvery
$current = 0

$results = [System.Collections.Generic.List[object]]::new()

# Recorrer los resultados
while (-not $rs.EOF) {
    $current += 1
    if ($Tabla -ieq "Kilometraje") {
        $results.Add([PSCustomObject]@{
            Unidad = $rs.Fields.Item($UnitField).Value
            Kilometros = Format-DecimalInvariant $rs.Fields.Item("Kms_diario").Value
            Fecha = Format-DateValue $rs.Fields.Item("Fecha").Value
            Observaciones = $rs.Fields.Item("Observaciones").Value
        })
    } else {
        $results.Add([PSCustomObject]@{
            Unidad = $rs.Fields.Item($UnitField).Value
            Fecha_desde = Format-DateValue $rs.Fields.Item("Fecha_desde").Value
            Fecha_hasta = Format-DateValue $rs.Fields.Item("Fecha_hasta").Value
            Fecha_est = Format-DateValue $rs.Fields.Item("Fecha_est").Value
            Intervencion = $rs.Fields.Item("Intervencion").Value
            Lugar = $rs.Fields.Item("Lugar").Value
            Observaciones = $rs.Fields.Item("Observaciones").Value
        })
    }
    if ($progressEvery -gt 0 -and ($current % $progressEvery -eq 0)) {
        if ($totalRows -gt 0) {
            $percent = [math]::Round(($current / $totalRows) * 100, 1)
            [Console]::Error.WriteLine("Progreso: $current/$totalRows ($percent%)")
        } else {
            [Console]::Error.WriteLine("Progreso: $current")
        }
    }
    try {
        $rs.MoveNext()
    } catch {
        [Console]::Error.WriteLine("Error al avanzar el recordset. Corte limpio para evitar COMException de marcador: $($_.Exception.Message)")
        break
    }
}

$conn.Close()

if ($current -gt 0) {
    if ($totalRows -gt 0) {
        $percent = [math]::Round(($current / $totalRows) * 100, 1)
        [Console]::Error.WriteLine("Progreso final: $current/$totalRows ($percent%)")
    } else {
        [Console]::Error.WriteLine("Progreso final: $current")
    }
}

# Emit JSON to stdout for downstream processing
if ($current -eq 0) {
    [Console]::Out.Write("[]")
    exit 0
}
$json = $results | ConvertTo-Json -Depth 4 -Compress
[Console]::Out.Write($json)
