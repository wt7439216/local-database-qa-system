[CmdletBinding()]
param(
    [switch]$ValidateOnly,
    [switch]$NoBrowser,
    [ValidateRange(1, 65535)][int]$Port = 8765,
    [string]$ListenAddress = "",
    [string]$PythonPath = ""
)
$ErrorActionPreference = "Stop"
try {
    . (Join-Path $PSScriptRoot "migration_tools\launch_common.ps1")
    Invoke-V41Launch -Mode Source -ValidateOnly:$ValidateOnly -NoBrowser:$NoBrowser -Port $Port -ListenAddress $ListenAddress -PythonPath $PythonPath
    exit 0
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}

