# P5 Windows single-command verification (equivalent to `make check`).
param(
    [switch]$Full,
    [string]$Out = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { $Python = "python" }

$Arguments = @("-X", "utf8", (Join-Path $ProjectRoot "scripts\verify_all.py"))
if ($Full) { $Arguments += "--full" }
if ($Out) { $Arguments += @("--out", $Out) }

Push-Location $ProjectRoot
try {
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) { throw "verify_all failed with exit code $LASTEXITCODE" }
}
finally {
    Pop-Location
}
