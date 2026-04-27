Param(
    [string]$EnvName = "shironosuke-pet-hospital",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$venvPython = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Host "检测到项目虚拟环境，优先使用 .venv 启动..." -ForegroundColor Green
    $env:HTTP_PROXY = ""
    $env:HTTPS_PROXY = ""
    $env:ALL_PROXY = ""
    $env:http_proxy = ""
    $env:https_proxy = ""
    $env:all_proxy = ""
    $env:NO_PROXY = "127.0.0.1,localhost"
    & $venvPython -m uvicorn backend.main:app --reload --host 127.0.0.1 --port $Port
    exit $LASTEXITCODE
}

$conda = $null
$candidates = @(
    "conda",
    "$env:USERPROFILE\miniconda3\Scripts\conda.exe",
    "$env:USERPROFILE\Miniconda3\Scripts\conda.exe"
)

foreach ($candidate in $candidates) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $conda = $candidate
        break
    }
    if (Test-Path $candidate) {
        $conda = $candidate
        break
    }
}

if (-not $conda) {
    throw "conda not found"
}

$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""
$env:ALL_PROXY = ""
$env:http_proxy = ""
$env:https_proxy = ""
$env:all_proxy = ""
$env:NO_PROXY = "127.0.0.1,localhost"

$envFile = Join-Path $PSScriptRoot 'environment.yml'
$envList = & $conda env list
$envExists = $false
foreach ($line in $envList) {
    if ($line.TrimStart().StartsWith($EnvName + " ")) {
        $envExists = $true
        break
    }
}

if (-not $envExists) {
    & $conda env create -f $envFile -n $EnvName
}

& $conda run -n $EnvName python -m uvicorn backend.main:app --reload --port $Port

