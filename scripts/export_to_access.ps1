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
    [string]$DbPassword = "",

    [Parameter(Mandatory=$false)]
    [ValidateSet("Locs", "Coche")]
    [string]$UnitField = "Locs"
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
WHERE [${UnitField}] = '$Unidad' 
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
    
    # ADODB constants
    $adCmdText = 1
    $adParamInput = 1
    $adDate = 7
    $adInteger = 3
    # Use ANSI text parameter types for Jet compatibility on server environments
    $adVarChar = 200
    $adLongVarChar = 201

    # Normalize values preserving NULL semantics
    $fecha_desde_value = [datetime]$Data.Fecha_desde
    $fecha_hasta_value = $null
    if ($Data.Fecha_hasta -and $Data.Fecha_hasta -ne "") {
        $fecha_hasta_value = [datetime]$Data.Fecha_hasta
    }

    $fecha_est_value = $null
    if ($Data.Fecha_est -and $Data.Fecha_est -ne "") {
        $fecha_est_value = [datetime]$Data.Fecha_est
    }

    $lugar_value = $null
    if ($Data.Lugar -and $Data.Lugar -ne "") {
        try {
            $lugar_value = [int]$Data.Lugar
        } catch {
            $lugar_value = $Data.Lugar
        }
    }

    $observaciones_value = $null
    if ($Data.Observaciones -and $Data.Observaciones -ne "") {
        $observaciones_value = [string]$Data.Observaciones
    }

    # Jet can fail on optional NULL params in fixed placeholder lists.
    # Build expressions so optional values use SQL NULL literals when absent.
    $fecha_hasta_expr = "NULL"
    if ($null -ne $fecha_hasta_value) {
        $fecha_hasta_expr = "?"
    }

    $fecha_est_expr = "NULL"
    if ($null -ne $fecha_est_value) {
        $fecha_est_expr = "?"
    }

    $observaciones_expr = "NULL"
    if ($null -ne $observaciones_value) {
        $observaciones_expr = "?"
    }

    $query = @"
INSERT INTO [Detenciones] (
    [${UnitField}], [Fecha_desde], [Fecha_hasta], [Fecha_est],
    [Intervencion], [Lugar], [Observaciones]
) VALUES (?, ?, $fecha_hasta_expr, $fecha_est_expr, ?, ?, $observaciones_expr)
"@
    
    try {
        $cmd = New-Object -ComObject ADODB.Command
        $cmd.ActiveConnection = $Conn
        $cmd.CommandType = $adCmdText
        $cmd.CommandText = $query

        [void]$cmd.Parameters.Append($cmd.CreateParameter("p1", $adVarChar, $adParamInput, 255, [string]$Data.Unidad))
        [void]$cmd.Parameters.Append($cmd.CreateParameter("p2", $adDate, $adParamInput, 0, $fecha_desde_value))
        if ($null -ne $fecha_hasta_value) {
            [void]$cmd.Parameters.Append($cmd.CreateParameter("p3", $adDate, $adParamInput, 0, $fecha_hasta_value))
        }
        if ($null -ne $fecha_est_value) {
            [void]$cmd.Parameters.Append($cmd.CreateParameter("p4", $adDate, $adParamInput, 0, $fecha_est_value))
        }
        [void]$cmd.Parameters.Append($cmd.CreateParameter("p5", $adVarChar, $adParamInput, 255, [string]$Data.Intervencion))

        if ($null -ne $lugar_value -and $lugar_value -is [int]) {
            [void]$cmd.Parameters.Append($cmd.CreateParameter("p6", $adInteger, $adParamInput, 0, $lugar_value))
        } else {
            [void]$cmd.Parameters.Append($cmd.CreateParameter("p6", $adVarChar, $adParamInput, 255, $lugar_value))
        }

        # Long text parameter to preserve multiline/large observaciones
        # NOTE: Jet OLEDB needs adParamLong attribute to avoid 255-char truncation.
        if ($null -ne $observaciones_value) {
            $obsSize = [Math]::Max(1, $observaciones_value.Length)
            $obsParam = $cmd.CreateParameter("p7", $adLongVarChar, $adParamInput, $obsSize, $observaciones_value)
            $obsParam.Attributes = 128  # adParamLong
            [void]$cmd.Parameters.Append($obsParam)
        }

        [void]$cmd.Execute()

        # Insert succeeded. Try to resolve identity, but don't fail export if this query is unsupported.
        try {
            $idRs = $Conn.Execute("SELECT @@IDENTITY")
            if ($idRs -and -not $idRs.EOF) {
                $newId = $idRs.Fields.Item(0).Value
                [Console]::Error.WriteLine("Novedad insertada con ID: $newId")
                return $newId
            }
        } catch {
            [Console]::Error.WriteLine("Insert ok, no se pudo obtener ID por @@IDENTITY: $($_.Exception.Message)")
        }

        [Console]::Error.WriteLine("Novedad insertada (sin ID devuelto)")
        return 0
    } catch {
        $msg = $_.Exception.Message
        # Check for FK error - return special code
        if ($msg -like "*se necesita un registro relacionado*" -or $msg -like "*registro relacionado*" -or $msg -like "*related record*") {
            $unitParentTable = if ($UnitField -ieq "Coche") { "Coches" } else { "Locomotoras" }
            $unitParentCol = if ($UnitField -ieq "Coche") { "Coche" } else { "Locs" }

            $unitExists = "unknown"
            $intervExists = "unknown"
            $lugarExists = "unknown"

            try {
                $rsU = $Conn.Execute("SELECT COUNT(*) AS C FROM [$unitParentTable] WHERE [$unitParentCol] = '$($Data.Unidad)'")
                if ($rsU -and -not $rsU.EOF) { $unitExists = [string]$rsU.Fields.Item("C").Value }
            } catch {
                $unitExists = "query_error"
            }

            try {
                $rsI = $Conn.Execute("SELECT COUNT(*) AS C FROM [Intervenciones] WHERE [Intervencion_tipo] = '$($Data.Intervencion)'")
                if ($rsI -and -not $rsI.EOF) { $intervExists = [string]$rsI.Fields.Item("C").Value }
            } catch {
                $intervExists = "query_error"
            }

            try {
                $rsL = $Conn.Execute("SELECT COUNT(*) AS C FROM [Lugares] WHERE [Lugar_codigo] = $($Data.Lugar)")
                if ($rsL -and -not $rsL.EOF) { $lugarExists = [string]$rsL.Fields.Item("C").Value }
            } catch {
                $lugarExists = "query_error"
            }

            [Console]::Error.WriteLine("FK_ERROR:Error de clave foránea (unit_field=$UnitField, unidad=$($Data.Unidad), intervencion=$($Data.Intervencion), lugar=$($Data.Lugar), unit_exists=$unitExists, intervencion_exists=$intervExists, lugar_exists=$lugarExists)")
        } else {
            [Console]::Error.WriteLine("Error inserting: $msg")
        }
        return $null
    }
}

function Get-SafeErrorMessage {
    param([string]$Message)

    if (-not $DbPassword -or $DbPassword -eq "") {
        return $Message
    }

    return $Message.Replace($DbPassword, "***")
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
    [Console]::Error.WriteLine("Mensaje original: $(Get-SafeErrorMessage -Message $_.Exception.Message)")
    exit 1
}

# Execute operation
$result = $null
$operationSucceeded = $false

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
            $operationSucceeded = $true
        } else {
            $operationSucceeded = $false
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
        if ($null -ne $result) {
            $operationSucceeded = $true
            if ($result -is [int] -and $result -gt 0) {
                [Console]::Out.WriteLine($result)
            }
        } else {
            $operationSucceeded = $false
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
            $operationSucceeded = $true
        } else {
            $operationSucceeded = $false
        }
    }
}

$conn.Close()

if ($operationSucceeded) {
    exit 0
} else {
    exit 1
}
