[CmdletBinding()]
param(
    [switch]$ValidateOnly,
    [switch]$NoBrowser,
    [ValidateRange(1, 65535)][int]$Port = 8765,
    [string]$ListenAddress = ""
)
$ErrorActionPreference = "Stop"
try {
    . (Join-Path $PSScriptRoot "migration_tools\launch_common.ps1")
    Invoke-V41Launch -Mode Exe -ValidateOnly:$ValidateOnly -NoBrowser:$NoBrowser -Port $Port -ListenAddress $ListenAddress
    exit 0
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}

