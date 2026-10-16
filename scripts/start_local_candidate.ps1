[CmdletBinding()]
param(
    [switch]$ValidateOnly,
    [switch]$NoBrowser,
    [ValidateRange(1, 65535)][int]$Port = 8765
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PointerPath = Join-Path $ProjectRoot "current_local_candidate.json"

function Get-RawSha256([string]$Path) {
    $Hasher = [System.Security.Cryptography.SHA256]::Create()
    $Stream = [System.IO.File]::OpenRead($Path)
    try { return -join ($Hasher.ComputeHash($Stream) | ForEach-Object { $_.ToString("x2") }) }
    finally { $Stream.Dispose(); $Hasher.Dispose() }
}

try {
    if (-not (Test-Path -LiteralPath $PointerPath -PathType Leaf)) {
        throw "No verified local candidate is activated. Complete REL-01 before starting this launcher. The old runtime was preserved."
    }
    $Pointer = Get-Content -LiteralPath $PointerPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($Pointer.schema_version -ne 1 -or $Pointer.status -ne "EXE_SMOKE_PASS_ACTIVATED") {
        throw "The local candidate pointer is not an accepted EXE smoke activation."
    }
    $BundleRoot = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $Pointer.bundle_path))
    if (-not (Test-Path -LiteralPath $BundleRoot -PathType Container)) {
        if ($Pointer.absolute_bundle_fallback -and (Test-Path -LiteralPath $Pointer.absolute_bundle_fallback -PathType Container)) {
            $BundleRoot = [System.IO.Path]::GetFullPath($Pointer.absolute_bundle_fallback)
        }
        else { throw "Activated candidate folder not found: $BundleRoot" }
    }
    $RecordPath = Join-Path $BundleRoot "BUILD_RECORD.json"
    $ExePath = Join-Path $BundleRoot "LocalDatabaseQA.exe"
    $ManifestPath = Join-Path $BundleRoot "build_manifest.json"
    if ((Get-RawSha256 $RecordPath) -ne $Pointer.build_record_raw_sha256) {
        throw "BUILD_RECORD identity differs from the accepted activation."
    }
    $Record = Get-Content -LiteralPath $RecordPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($Record.version -ne $Pointer.version -or $Record.production_source_hash -ne $Pointer.production_source_hash) {
        throw "Candidate version or production identity differs from the activation."
    }
    if ((Get-RawSha256 $ExePath) -ne $Pointer.exe_raw_sha256 -or $Record.exe_raw_sha256 -ne $Pointer.exe_raw_sha256) {
        throw "Executable identity differs from the accepted candidate."
    }
    if ((Get-RawSha256 $ManifestPath) -ne $Record.files.'build_manifest.json') {
        throw "Build manifest identity differs from the accepted build."
    }
    $Manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($Manifest.version -ne $Pointer.version -or $Manifest.source_identity.production_source_hash -ne $Pointer.production_source_hash) {
        throw "Packaged source manifest differs from the activation."
    }
    $LaunchIdentity = [ordered]@{
        timestamp = [DateTimeOffset]::Now.ToString("o")
        version = $Pointer.version
        executable = $ExePath
        build_record_raw_sha256 = $Pointer.build_record_raw_sha256
        exe_raw_sha256 = $Pointer.exe_raw_sha256
        production_source_hash = $Pointer.production_source_hash
        quality_status = $Manifest.quality_evidence.status
        mode = $(if ($ValidateOnly) { "VALIDATE_ONLY" } else { "LAUNCH" })
    }
    if ($ValidateOnly) {
        $LaunchIdentity | ConvertTo-Json -Compress
        exit 0
    }
    $Ollama = Get-Command ollama.exe -ErrorAction SilentlyContinue
    if (-not $Ollama) { throw "Ollama is not installed. Install it, bge-m3, and qwen2.5:7b first." }
    & $Ollama.Source list *> $null
    if ($LASTEXITCODE -ne 0) {
        Start-Process -FilePath $Ollama.Source -ArgumentList @("serve") -WindowStyle Hidden
        Start-Sleep -Seconds 2
    }
    if (-not $env:LIBRARY_IMPORT_ROOTS) {
        $ImportRoot = Join-Path $BundleRoot "import_sources"
        $null = New-Item -ItemType Directory -Path $ImportRoot -Force
        $env:LIBRARY_IMPORT_ROOTS = $ImportRoot
    }
    $LogRoot = Join-Path $BundleRoot "_internal\data\logs"
    $null = New-Item -ItemType Directory -Path $LogRoot -Force
    ($LaunchIdentity | ConvertTo-Json -Compress) | Add-Content -LiteralPath (Join-Path $LogRoot "local_launcher.jsonl") -Encoding UTF8
    Write-Host "Starting $($Pointer.version) from $ExePath"
    Write-Host "Build record SHA256: $($Pointer.build_record_raw_sha256)"
    $LaunchArguments = @("--port", [string]$Port)
    if ($NoBrowser) { $LaunchArguments += "--no-browser" }
    Start-Process -FilePath $ExePath -WorkingDirectory $BundleRoot -ArgumentList $LaunchArguments -WindowStyle Hidden
    exit 0
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
