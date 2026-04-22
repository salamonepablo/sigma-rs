# Export Novedades from SQLite to Access .mdb
# Supports INSERT, UPDATE, and CHECK operations

param(
    [Parameter(Mandatory=$true)]
    [string]$DbPath,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("INSERT", "UPDATE", "CHECK")]
    [string]$Operation = "INSERT",
    
    # For CHECK/INSERT/UPDATE - PK fields
    [Parameter(Mandatory=$false)]
    [string]$Unidad = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Fecha_hasta = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Intervencion = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Lugar = "",
    
    # For INSERT - additional fields
    [Parameter(Mandatory=$false)]
    [string]$Fecha_desde = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Fecha_est = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Observaciones = "",

    [Parameter(Mandatory=$false)]
    [string]$DbPassword = ""
)

$invariantCulture = [System.Globalization.CultureInfo]::InvariantCulture

function Get-DateValue {
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

function Test-NovedadExistsInAccess {
    param(
        [object]$Conn,
        [string]$Unidad,
        [string]$Fecha_hasta,
        [string]$Intervencion,
        [string]$Lugar
    )
    
    # Build query - handle NULL fecha_hasta properly
    $fecha_hasta_clause = ""
    if ($Fecha_hasta -and $Fecha_hasta -ne "") {
        $fecha_hasta_clause = "AND [Fecha_hasta] = #$Fecha_hasta#"
    } else {
        # For NULL fecha_hasta in Access
        $fecha_hasta_clause = "AND [Fecha_hasta] IS NULL"
    }
    
    $query = @"
SELECT [ID] FROM [Detenciones] 
WHERE [Locs] = '$Unidad' 
AND [Intervencion] = '$Intervencion' 
AND [Lugar] = '$Lugar' 
$fecha_hasta_clause
"@
    
try {
        $rs = New-Object -ComObject ADODB.Recordset
        $rs.CursorLocation = 3
        $rs.CursorType = 1  # adOpenKeyset
        $rs.LockType = 1  # adLockOptimistic
        $rs.Open($query, $Conn)
        if ($rs -and -not $rs.EOF) {
            $id = $rs.Fields.Item("ID").Value
            $rs.Close()
            return $id
        }
        $rs.Close()
        return $null
    } catch {
        [Console]::Error.WriteLine("Error checking existencia: $($_.Exception.Message)")
        return $null
    }
}

function Add-NovedadToAccess {
    param(
        [object]$Conn,
        [hashtable]$Data
    )
    
    # Format fecha_hasta - handle NULL
    $fecha_hasta_sql = "NULL"
    if ($Data.Fecha_hasta -and $Data.Fecha_hasta -ne "") {
        $fecha_hasta_sql = "#$($Data.Fecha_hasta)#"
    }
    
    # Format fecha_desde
    $fecha_desde_sql = "#$($Data.Fecha_desde)#"
    
    # Format fecha_est - handle NULL
    $fecha_est_sql = "NULL"
    if ($Data.Fecha_est -and $Data.Fecha_est -ne "") {
        $fecha_est_sql = "#$($Data.Fecha_est)#"
    }
    
    # Escape Observaciones
    $observaciones_sql = "NULL"
    if ($Data.Observaciones -and $Data.Observaciones -ne "") {
        $obs = $Data.Observaciones.Replace("'", "''")
        $observaciones_sql = "'$obs'"
    }
    
    $query = @"
INSERT INTO [Detenciones] (
    [Locs], [Fecha_desde], [Fecha_hasta], [Fecha_est], 
    [Intervencion], [Lugar], [Observaciones]
) VALUES (
    '$($Data.Unidad)', 
    $fecha_desde_sql, 
    $fecha_hasta_sql, 
    $fecha_est_sql, 
    '$($Data.Intervencion)', 
    '$($Data.Lugar)', 
    $observaciones_sql
)
"@
    
    try {
        $Conn.Execute($query)
        
        # Get the ID of inserted record
        $idRs = New-Object -ComObject ADODB.Recordset
        $idRs.CursorLocation = 3
        $idRs.Open("SELECT @@IDENTITY", $Conn)
        if ($idRs -and -not $idRs.EOF) {
            $newId = $idRs.Fields.Item(0).Value
        } else {
            $newId = 0
        }
        $idRs.Close()
        
        [Console]::Error.WriteLine("Novedad insertada con ID: $newId")
        return $newId
    } catch {
        $msg = $_.Exception.Message
        # Check for FK error - return special code
        if ($msg -like "*se necesita un registro relacionado*") {
            [Console]::Error.WriteLine("FK_ERROR:Lugar no existe en tabla Lugares")
        } else {
            [Console]::Error.WriteLine("Error inserting: $msg")
        }
        return $null
    }
}

function Update-NovedadInAccess {
    param(
        [object]$Conn,
        [int]$LegacyId,
        [hashtable]$Data
    )
    
    # Format fecha_hasta - handle NULL
    $fecha_hasta_set = ""
    if ($Data.Fecha_hasta -and $Data.Fecha_hasta -ne "") {
        $fecha_hasta_set = "[Fecha_hasta] = #$($Data.Fecha_hasta)#, "
    }
    
    # Escape Observaciones
    $observaciones_set = ""
    if ($Data.Observaciones -and $Data.Observaciones -ne "") {
        $obs = $Data.Observaciones.Replace("'", "''")
        $observaciones_set = "[Observaciones] = '$obs', "
    }
    
    $query = @"
UPDATE [Detenciones] SET 
    $fecha_hasta_set
    $observaciones_set
    [Fecha_est] = $(if ($Data.Fecha_est -and $Data.Fecha_est -ne "") { "#$($Data.Fecha_est)#" } else { "NULL" })
WHERE [ID] = $LegacyId
"@
    
    try {
        $Conn.Execute($query)
        [Console]::Error.WriteLine("Novedad $LegacyId actualizada")
        return $true
    } catch {
        [Console]::Error.WriteLine("Error updating: $($_.Exception.Message)")
        return $false
    }
}

# Main execution
if (-not $DbPath -or -not (Test-Path $DbPath)) {
    Write-Output "ERROR: DbPath invalido o inexistente: $DbPath"
    exit 1
}

# Connection string
$passwordSegment = ""
if ($DbPassword) {
    $passwordSegment = "Jet OLEDB:Database Password=$DbPassword;"
}
$connStringACE = "Provider=Microsoft.ACE.OLEDB.12.0;Data Source=$DbPath;$passwordSegment"
$connStringJet = "Provider=Microsoft.Jet.OLEDB.4.0;Data Source=$DbPath;$passwordSegment"

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
    exit 1
}

# Execute operation
$result = $null

switch ($Operation) {
    "CHECK" {
        if (-not $Unidad -or -not $Intervencion -or -not $Lugar) {
            [Console]::Error.WriteLine("CHECK requiere: -Unidad, -Intervencion, -Lugar")
            $conn.Close()
            exit 1
        }
        $result = Test-NovedadExistsInAccess -Conn $conn -Unidad $Unidad -Fecha_hasta $Fecha_hasta -Intervencion $Intervencion -Lugar $Lugar
        if ($result) {
            [Console]::Out.WriteLine($result)
        }
    }
    "INSERT" {
        if (-not $Unidad -or -not $Fecha_desde -or -not $Intervencion -or -not $Lugar) {
            [Console]::Error.WriteLine("INSERT requiere: -Unidad, -Fecha_desde, -Intervencion, -Lugar")
            $conn.Close()
            exit 1
        }
        $novedadData = @{
            Unidad = $Unidad
            Fecha_desde = $Fecha_desde
            Fecha_hasta = $Fecha_hasta
            Fecha_est = $Fecha_est
            Intervencion = $Intervencion
            Lugar = $Lugar
            Observaciones = $Observaciones
        }
        $result = Add-NovedadToAccess -Conn $conn -Data $novedadData
        if ($result) {
            [Console]::Out.WriteLine($result)
        }
    }
    "UPDATE" {
        if (-not $Unidad -or -not $Intervencion -or -not $Lugar) {
            [Console]::Error.WriteLine("UPDATE requiere: -Unidad, -Intervencion, -Lugar")
            $conn.Close()
            exit 1
        }
        # First check if exists
        $legacyId = Test-NovedadExistsInAccess -Conn $conn -Unidad $Unidad -Fecha_hasta $Fecha_hasta -Intervencion $Intervencion -Lugar $Lugar
        if (-not $legacyId) {
            [Console]::Error.WriteLine("No se encontró registro para actualizar")
            $conn.Close()
            exit 1
        }
        
        $novedadData = @{
            Unidad = $Unidad
            Fecha_hasta = $Fecha_hasta
            Fecha_est = $Fecha_est
            Observaciones = $Observaciones
        }
        $result = Update-NovedadInAccess -Conn $conn -LegacyId $legacyId -Data $novedadData
        if ($result) {
            [Console]::Out.WriteLine($legacyId)
        }
    }
}

$conn.Close()

if ($result) {
    exit 0
} else {
    exit 1
}