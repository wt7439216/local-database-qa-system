[CmdletBinding()]
param(
    [string]$Python = "python",
    [string]$LibraryPath = "",
    [string]$OutputRoot = "",
    [string]$BuildRoot = "",
    [string]$Version = "4.0.0-alpha.3",
    [string]$ExpectedProductionHash = "",
    [string]$QualityEvidence = "",
    [switch]$SkipInstall,
    [switch]$SkipTests,
    [switch]$Preflight,
    # Kept for existing local invocations. Builds never rebuild a library.
    [switch]$SkipIndex
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SpecPath = Join-Path $ProjectRoot "windows_desktop.spec"
$BundleTool = Join-Path $ProjectRoot "scripts\windows_bundle.py"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
if (-not $LibraryPath) { $LibraryPath = Join-Path $ProjectRoot "data\library\documents.sqlite3" }
if (-not $OutputRoot) { $OutputRoot = Join-Path (Split-Path -Parent $ProjectRoot) "KB-V4_Candidates\$Version-$Stamp" }
if (-not $BuildRoot) { $BuildRoot = Join-Path (Split-Path -Parent $ProjectRoot) "KB-V4_Recovery\build-$Stamp" }
$OutputRoot = [System.IO.Path]::GetFullPath($OutputRoot)
$BuildRoot = [System.IO.Path]::GetFullPath($BuildRoot)
$SeedRoot = Join-Path $BuildRoot "bundle-seed"
$ExePath = Join-Path $OutputRoot "LocalDatabaseQA\LocalDatabaseQA.exe"
$OldSeedRoot = $env:QA_BUNDLE_SEED_ROOT

function Invoke-Checked {
    param([scriptblock]$Command, [string]$Description)
    Write-Host "`n==> $Description" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "$Description failed with exit code $LASTEXITCODE." }
}

# Refuse replacement even when PyInstaller could overwrite an old package.
if (Test-Path -LiteralPath $OutputRoot) { throw "OutputRoot already exists; choose a new directory: $OutputRoot" }
if (Test-Path -LiteralPath $SeedRoot) { throw "Build seed already exists; choose a new BuildRoot: $SeedRoot" }

Push-Location $ProjectRoot
try {
    Invoke-Checked -Description "Checking build Python (3.10-3.12 required by RapidOCR 1.4)" -Command {
        & $Python -c "import sys; print(sys.version); assert (3,10) <= sys.version_info[:2] < (3,13), 'Use a dedicated Python 3.12 build environment; do not ignore dependency Python requirements.'"
    }
    if (-not $SkipInstall) {
        Invoke-Checked -Description "Installing the complete five-format build profile" -Command {
            & $Python -m pip install -r (Join-Path $ProjectRoot "requirements-build.txt")
        }
    }
    Invoke-Checked -Description "Checking installed dependency compatibility" -Command {
        & $Python -m pip check
        if ($LASTEXITCODE -ne 0) { throw "pip check failed." }
        & $Python -X utf8 $BundleTool check-environment
    }
    $PrepareArgs = @("-X", "utf8", $BundleTool, "prepare", "--library", $LibraryPath, "--seed-root", $SeedRoot, "--version", $Version)
    if ($ExpectedProductionHash) { $PrepareArgs += @("--expected-production-hash", $ExpectedProductionHash) }
    if ($QualityEvidence) { $PrepareArgs += @("--quality-evidence", $QualityEvidence) }
    if ($Preflight) { $PrepareArgs += "--preflight" }
    Invoke-Checked -Description "Preparing a byte-verified managed-library snapshot (no rebuild)" -Command {
        & $Python @PrepareArgs
    }
    if (-not $SkipTests) {
        Invoke-Checked -Description "Running source regression tests" -Command {
            & $Python -X utf8 -m unittest discover -v
        }
    }
    $env:QA_BUNDLE_SEED_ROOT = $SeedRoot
    Invoke-Checked -Description "Building a separate Windows development candidate" -Command {
        & $Python -m PyInstaller --noconfirm --clean --log-level WARN --distpath $OutputRoot --workpath (Join-Path $BuildRoot "pyinstaller") $SpecPath
    }
    if (-not (Test-Path -LiteralPath $ExePath -PathType Leaf)) { throw "Expected EXE missing: $ExePath" }
    Invoke-Checked -Description "Verifying packaged data, source identity, and executable modules" -Command {
        & $Python -X utf8 $BundleTool finalize --seed-root $SeedRoot --bundle-root (Split-Path -Parent $ExePath)
    }
    Write-Host "`nBuild completed: $ExePath" -ForegroundColor Green
    Write-Host "Distribute the complete LocalDatabaseQA folder. The original runtime folder was preserved."
    Write-Host "The candidate still requires its recorded EXE smoke checks and quality verdict. Build files are retained at $BuildRoot."
}
finally {
    if ($null -eq $OldSeedRoot) { Remove-Item Env:\QA_BUNDLE_SEED_ROOT -ErrorAction SilentlyContinue }
    else { $env:QA_BUNDLE_SEED_ROOT = $OldSeedRoot }
    Pop-Location
}
