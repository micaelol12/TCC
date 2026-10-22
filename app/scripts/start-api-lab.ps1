$ErrorActionPreference = 'Stop'
$apiDirectory = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../api'))
$previousEnvironment = $env:APP_ENV
$previousExperimental = $env:EXPERIMENTAL_CONFIG_ENABLED
try {
    $env:APP_ENV = 'lab'
    $env:EXPERIMENTAL_CONFIG_ENABLED = 'true'
    Set-Location -LiteralPath $apiDirectory
    $pythonExecutable = Join-Path $apiDirectory '.venv/Scripts/python.exe'
    if (-not (Test-Path -LiteralPath $pythonExecutable)) { $pythonExecutable = 'python' }
    & $pythonExecutable -m uvicorn app.main:app --host 127.0.0.1 --port 8001
    exit $LASTEXITCODE
} finally {
    $env:APP_ENV = $previousEnvironment
    $env:EXPERIMENTAL_CONFIG_ENABLED = $previousExperimental
}
