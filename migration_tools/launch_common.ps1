[CmdletBinding()]
param()

$script:V41MigrationProjectRoot = Split-Path -Parent $PSScriptRoot

function Get-V41RawSha256([string]$LiteralPath) {
    $Hasher = [System.Security.Cryptography.SHA256]::Create()
    $Stream = [System.IO.File]::OpenRead($LiteralPath)
    try { return -join ($Hasher.ComputeHash($Stream) | ForEach-Object { $_.ToString("x2") }) }
    finally { $Stream.Dispose(); $Hasher.Dispose() }
}

function Get-V41LocalModels([string]$ModelRoot) {
    $Models = @()
    foreach ($Spec in @(
        @{ Name = "bge-m3:latest"; RelativeManifest = "manifests\registry.ollama.ai\library\bge-m3\latest" },
        @{ Name = "qwen2.5:7b"; RelativeManifest = "manifests\registry.ollama.ai\library\qwen2.5\7b" }
    )) {
        $ManifestPath = Join-Path $ModelRoot $Spec.RelativeManifest
        if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
            throw "Required local model manifest missing: $ManifestPath"
        }
        $Manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($Blob in @($Manifest.config) + @($Manifest.layers)) {
            if (-not $Blob.digest -or $Blob.digest -notmatch "^sha256:[a-fA-F0-9]{64}$") {
                throw "Invalid model blob identity in $ManifestPath"
            }
            $BlobPath = Join-Path $ModelRoot ("blobs\" + ($Blob.digest -replace ":", "-"))
            if (-not (Test-Path -LiteralPath $BlobPath -PathType Leaf)) {
                throw "Required model blob missing: $BlobPath"
            }
            if ((Get-Item -LiteralPath $BlobPath).Length -ne [long]$Blob.size) {
                throw "Model blob size differs from its manifest: $BlobPath"
            }
        }
        $Models += [pscustomobject]@{
            name = $Spec.Name
            manifest = $ManifestPath
            digest = Get-V41RawSha256 $ManifestPath
        }
    }
    return $Models
}

function Get-V41PythonProfile([string]$PythonPath) {
    if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
        throw "Target source environment is missing: $PythonPath. Create .venv with Python 3.12 and install requirements-ingest.txt."
    }
    $Probe = @'
import importlib.metadata as m
import json
import re
import sys
required = {'PyMuPDF': (1, 24), 'rapidocr-onnxruntime': (1, 4), 'python-docx': (1, 1), 'python-pptx': (1, 0)}
versions = {}
errors = []
if not ((3, 10) <= sys.version_info[:2] < (3, 13)):
    errors.append('Complete OCR profile requires Python 3.10-3.12; Python 3.12 is recommended.')
for name, minimum in required.items():
    try:
        version = m.version(name)
        versions[name] = version
        numbers = tuple(int(x) for x in re.findall(r'\d+', version)[:2])
        if numbers < minimum or numbers[0] >= 2:
            errors.append(name + ' version is outside requirements-ingest.txt: ' + version)
    except m.PackageNotFoundError:
        errors.append('Missing dependency: ' + name)
print(json.dumps({'executable': sys.executable, 'python': sys.version, 'packages': versions, 'errors': errors}))
sys.exit(0 if not errors else 1)
'@
    $ProbeOutput = & $PythonPath -B -c $Probe
    $ProbeExit = $LASTEXITCODE
    if (-not $ProbeOutput) { throw "Could not inspect target Python environment: $PythonPath" }
    $Profile = ($ProbeOutput -join [Environment]::NewLine) | ConvertFrom-Json
    if ($ProbeExit -ne 0) {
        throw ("Target source environment does not provide the complete ingestion profile: " + ($Profile.errors -join "; "))
    }
    return $Profile
}

function Get-V41Context(
    [ValidateSet("Exe", "Source")][string]$Mode,
    [string]$PythonPath = ""
) {
    $ProjectRoot = $script:V41MigrationProjectRoot
    $ModelRoot = Join-Path $ProjectRoot "model"
    $BundleRoot = Join-Path $ProjectRoot "runtime\LocalDatabaseQA"
    $Models = @(Get-V41LocalModels $ModelRoot)
    if ($Mode -eq "Exe") {
        $ImportRoot = Join-Path $BundleRoot "import_sources"
        $LibraryPath = Join-Path $BundleRoot "_internal\data\library\documents.sqlite3"
    }
    else {
        $ImportRoot = Join-Path $ProjectRoot "import_sources"
        $LibraryPath = Join-Path $ProjectRoot "data\library\documents.sqlite3"
        if (-not $PythonPath) { $PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe" }
        $PythonPath = [System.IO.Path]::GetFullPath($PythonPath)
    }
    if (-not (Test-Path -LiteralPath $LibraryPath -PathType Leaf)) {
        throw "Expected migrated managed library missing: $LibraryPath. No empty library will be created by this launcher."
    }
    $Context = [ordered]@{
        mode = $Mode
        project_root = $ProjectRoot
        model_root = $ModelRoot
        ollama_url = "http://127.0.0.1:11434"
        import_root = $ImportRoot
        library_path = $LibraryPath
        models = $Models
    }
    if ($Mode -eq "Source") {
        $Context.python_path = $PythonPath
        $Context.python_profile = Get-V41PythonProfile $PythonPath
    }
    else {
        $LegacyLauncher = Join-Path $ProjectRoot "scripts\start_local_candidate.ps1"
        $ValidationOutput = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $LegacyLauncher -ValidateOnly
        if ($LASTEXITCODE -ne 0) { throw "The migrated candidate failed the original activation identity check." }
        $Context.candidate_activation = ($ValidationOutput -join [Environment]::NewLine) | ConvertFrom-Json
        $Pointer = Get-Content -LiteralPath (Join-Path $ProjectRoot "current_local_candidate.json") -Raw -Encoding UTF8 | ConvertFrom-Json
        $ExpectedBundleRoot = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $Pointer.bundle_path))
        if ($ExpectedBundleRoot -ne [System.IO.Path]::GetFullPath($BundleRoot)) {
            throw "The migrated activation pointer does not select runtime\LocalDatabaseQA."
        }
        $SmokePath = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $Pointer.smoke_report_path))
        if ((Get-V41RawSha256 $SmokePath) -ne $Pointer.smoke_report_raw_sha256) {
            throw "The preserved original EXE smoke report does not match the activation."
        }
    }
    return [pscustomobject]$Context
}

function Set-V41ProcessEnvironment($Context, [string]$ListenAddress = "") {
    # Process scope only. Persistence and migration-time service restart are separate operations.
    $env:OLLAMA_MODELS = $Context.model_root
    $env:QA_OLLAMA_URL = $Context.ollama_url
    if ($ListenAddress) { $env:QA_DESKTOP_HOST = $ListenAddress }
    $env:LIBRARY_IMPORT_ROOTS = $Context.import_root
    $null = New-Item -ItemType Directory -Path $Context.import_root -Force
}

function Read-V41ServiceJson([string]$Url) {
    $Request = [System.Net.HttpWebRequest]::Create($Url)
    $Request.Method = "GET"
    $Request.Proxy = $null
    $Request.Timeout = 2000
    $Request.ReadWriteTimeout = 2000
    $Response = $null
    $Reader = $null
    try {
        $Response = $Request.GetResponse()
        $Reader = New-Object System.IO.StreamReader($Response.GetResponseStream())
        return ($Reader.ReadToEnd() | ConvertFrom-Json)
    }
    finally {
        if ($Reader) { $Reader.Dispose() }
        if ($Response) { $Response.Dispose() }
    }
}

function Ensure-V41Ollama($Context) {
    $Version = $null
    try { $Version = Read-V41ServiceJson ($Context.ollama_url + "/api/version") } catch {}
    $StartedPid = $null
    if (-not $Version -or -not $Version.version) {
        $Ollama = Get-Command ollama.exe -ErrorAction SilentlyContinue
        if (-not $Ollama) { throw "Ollama is not installed or ollama.exe is not available on PATH." }
        # Never stop or replace a running process. A new server inherits this launcher's model root.
        $StartedProcess = Start-Process -FilePath $Ollama.Source -ArgumentList @("serve") -WindowStyle Hidden -PassThru
        $StartedPid = $StartedProcess.Id
        for ($Attempt = 0; $Attempt -lt 20; $Attempt++) {
            Start-Sleep -Milliseconds 500
            try { $Version = Read-V41ServiceJson ($Context.ollama_url + "/api/version") } catch {}
            if ($Version -and $Version.version) { break }
        }
        if (-not $Version -or -not $Version.version) {
            throw "Ollama did not become available at $($Context.ollama_url). Check the existing service or port 11434."
        }
    }
    $Tags = Read-V41ServiceJson ($Context.ollama_url + "/api/tags")
    foreach ($Expected in $Context.models) {
        $Actual = @($Tags.models | Where-Object { $_.name -eq $Expected.name })
        if ($Actual.Count -ne 1 -or $Actual[0].digest -ne $Expected.digest) {
            throw "Running Ollama model identity differs from the migrated local manifest: $($Expected.name). No download or model inference was requested."
        }
    }
    # API model identity is checked; only a service restart can adopt a changed OLLAMA_MODELS.
    return [pscustomobject]@{ version = $Version.version; started_pid = $StartedPid; model_digests_match = $true }
}

function Invoke-V41Launch(
    [ValidateSet("Exe", "Source")][string]$Mode,
    [switch]$ValidateOnly,
    [switch]$NoBrowser,
    [ValidateRange(1, 65535)][int]$Port = 8765,
    [string]$ListenAddress = "",
    [string]$PythonPath = ""
) {
    $Context = Get-V41Context -Mode $Mode -PythonPath $PythonPath
    if ($ValidateOnly) {
        [pscustomobject]@{
            status = "OFFLINE_VALIDATION_PASS"
            service_requests = 0
            model_inference_requests = 0
            database_writes = 0
            context = $Context
        } | ConvertTo-Json -Depth 12
        return
    }
    Set-V41ProcessEnvironment -Context $Context -ListenAddress $ListenAddress
    $Service = Ensure-V41Ollama $Context
    if ($Mode -eq "Exe") {
        $LauncherArguments = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $Context.project_root "scripts\start_local_candidate.ps1"), "-Port", [string]$Port)
        if ($NoBrowser) { $LauncherArguments += "-NoBrowser" }
        & powershell.exe @LauncherArguments
        if ($LASTEXITCODE -ne 0) { throw "Verified candidate startup failed." }
        Write-Host "V4.1 EXE started. Model root: $($Context.model_root)"
    }
    else {
        $SourceArguments = @("-B", "-m", "desktop", "--port", [string]$Port)
        if ($NoBrowser) { $SourceArguments += "--no-browser" }
        $SourceProcess = Start-Process -FilePath $Context.python_path -WorkingDirectory $Context.project_root -ArgumentList $SourceArguments -WindowStyle Hidden -PassThru
        [pscustomobject]@{
            status = "SOURCE_PROCESS_STARTED"
            process_id = $SourceProcess.Id
            port_requested = $Port
            library_path = $Context.library_path
            model_root = $Context.model_root
            service = $Service
        } | ConvertTo-Json -Depth 8
    }
}

