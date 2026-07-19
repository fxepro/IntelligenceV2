param(
    [ValidateSet("tiny", "base", "small", "medium", "large-v3-turbo", "large-v3")]
    [string]$Model = "medium"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Bin = Join-Path $Root "bin"
$Models = Join-Path $Root "models"
$Cli = Join-Path $Bin "whisper-cli.exe"
$ModelFile = Join-Path $Models "ggml-$Model.bin"

New-Item -ItemType Directory -Force -Path $Bin, $Models | Out-Null

if (-not (Test-Path $Cli)) {
    $zip = Join-Path $env:TEMP "whisper-bin-x64-v1.9.1.zip"
    $extract = Join-Path $env:TEMP "whisper-bin-x64-v1.9.1"
    Write-Host "Downloading whisper.cpp v1.9.1..."
    Invoke-WebRequest `
        -Uri "https://github.com/ggml-org/whisper.cpp/releases/download/v1.9.1/whisper-bin-x64.zip" `
        -OutFile $zip
    Remove-Item -Recurse -Force $extract -ErrorAction SilentlyContinue
    Expand-Archive -Path $zip -DestinationPath $extract -Force
    Get-ChildItem -Path $extract -File -Recurse | Copy-Item -Destination $Bin -Force
    Remove-Item $zip -Force
    Remove-Item -Recurse -Force $extract
}

if (-not (Test-Path $ModelFile)) {
    Write-Host "Downloading Whisper model '$Model' (this may take a while)..."
    Invoke-WebRequest `
        -Uri "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-$Model.bin?download=true" `
        -OutFile $ModelFile
}

Write-Host "Whisper CLI: $Cli"
Write-Host "Model:       $ModelFile"
