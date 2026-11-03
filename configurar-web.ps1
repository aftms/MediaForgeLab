$ErrorActionPreference = 'Stop'
$configPath = Join-Path $PSScriptRoot 'config.local.json'
$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    $quotedScript = '"' + $PSCommandPath + '"'
    $process = Start-Process powershell.exe -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',$quotedScript -Verb RunAs -WindowStyle Hidden -Wait -PassThru
    exit $process.ExitCode
}
$ruleName = 'MagForgeLab-Web-HTTPS-Local'
if (Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue) {
    Remove-NetFirewallRule -Name $ruleName
}
New-NetFirewallRule -Name $ruleName -DisplayName 'Media Forge Lab HTTPS - rede de casa' -Direction Inbound -Action Allow -Protocol TCP -LocalPort $config.https_port -LocalAddress $config.host -RemoteAddress $config.allowed_network -Profile Private | Out-Null
Write-Output 'HTTPS permitido apenas no IP e na rede privada configurados.'
