$ErrorActionPreference = 'Stop'
$apiDirectory = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../api'))
$previousEnvironment = $env:APP_ENV
$previousExperimental = $env:EXPERIMENTAL_CONFIG_ENABLED
try {
    $env:APP_ENV = 'development'
    $env:EXPERIMENTAL_CONFIG_ENABLED = 'false'
    Set-Location -LiteralPath $apiDirectory
    $pythonExecutable = Join-Path $apiDirectory '.venv/Scripts/python.exe'
    if (-not (Test-Path -LiteralPath $pythonExecutable)) { $pythonExecutable = 'python' }
    & $pythonExecutable -m uvicorn app.main:app --host 127.0.0.1 --port 8000
    exit $LASTEXITCODE
} finally {
    $env:APP_ENV = $previousEnvironment
    $env:EXPERIMENTAL_CONFIG_ENABLED = $previousExperimental
}
