[CmdletBinding()]
param(
    [string]$Python = "python",
    [switch]$SkipInstall,
    [switch]$SkipIndex
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SpecPath = Join-Path $ProjectRoot "windows_desktop.spec"
$DesktopRoot = Join-Path $ProjectRoot "desktop"
$DistRoot = Join-Path $DesktopRoot "dist"
$BuildRoot = Join-Path $DesktopRoot "build"
$ExePath = Join-Path $DistRoot "LocalDatabaseQA\LocalDatabaseQA.exe"
$RequiredPyInstallerVersion = "6.21.0"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command,
        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    Write-Host "`n==> $Description" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

Push-Location $ProjectRoot
try {
    Invoke-Checked -Description "Checking Python" -Command {
        & $Python --version
    }

    & $Python -c "import PyInstaller, sys; print('PyInstaller', PyInstaller.__version__); sys.exit(0 if PyInstaller.__version__ == '$RequiredPyInstallerVersion' else 1)" 2>$null
    if ($LASTEXITCODE -ne 0) {
        if ($SkipInstall) {
            throw "PyInstaller $RequiredPyInstallerVersion is missing. Install it or remove -SkipInstall."
        }
        Invoke-Checked -Description "Installing PyInstaller $RequiredPyInstallerVersion" -Command {
            & $Python -m pip install "pyinstaller==$RequiredPyInstallerVersion"
        }
    }

    $RequiredFiles = @(
        (Join-Path $ProjectRoot "data\library\textbooks.sqlite3"),
        (Join-Path $ProjectRoot "web\index.html"),
        (Join-Path $ProjectRoot "web\app.js"),
        (Join-Path $ProjectRoot "web\styles.css")
    )

    if (-not $SkipIndex) {
        Invoke-Checked -Description "Building the structured textbook library" -Command {
            & $Python -X utf8 (Join-Path $ProjectRoot "scripts\build_library.py")
        }
    }

    $MissingFiles = @($RequiredFiles | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) })
    if ($MissingFiles.Count -gt 0) {
        throw "Required bundle data is missing: $($MissingFiles -join ', ')"
    }

    Invoke-Checked -Description "Validating the desktop entry point and knowledge base" -Command {
        & $Python -X utf8 -c "from core.engine_v2 import StructuredQAEngine; import desktop.web_main; e=StructuredQAEngine(); assert e.library.has_vectors; print(f'Knowledge base: {len(e.library.chunks)} chunks, {e.library.dimension} dimensions')"
    }

    Invoke-Checked -Description "Running all tests" -Command {
        & $Python -X utf8 -m unittest discover -v
    }

    Invoke-Checked -Description "Building the Windows desktop application" -Command {
        & $Python -m PyInstaller `
            --noconfirm `
            --clean `
            --log-level WARN `
            --distpath $DistRoot `
            --workpath $BuildRoot `
            $SpecPath
    }

    if (-not (Test-Path -LiteralPath $ExePath -PathType Leaf)) {
        throw "The build completed without producing the expected EXE: $ExePath"
    }

    $Exe = Get-Item -LiteralPath $ExePath
    Write-Host "`nBuild completed" -ForegroundColor Green
    Write-Host "EXE: $($Exe.FullName)"
    Write-Host "Size: $([math]::Round($Exe.Length / 1MB, 2)) MB"
    Write-Host "Distribute the complete LocalDatabaseQA folder, not just the EXE."
}
finally {
    Pop-Location
}
