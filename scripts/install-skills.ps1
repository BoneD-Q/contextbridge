# Install ContextBridge skills into host discovery directories (.agents / .claude / .cursor).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
python "$PSScriptRoot\install_skills.py" @args
exit $LASTEXITCODE
