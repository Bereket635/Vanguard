<#
.SYNOPSIS
    Run SharpHound (BloodHound CE collector) and package the output as a ZIP.
.DESCRIPTION
    Requires SharpHound.ps1 in the same folder or on PATH.
    Output ZIP is directly uploadable to the Vanguard backend.
#>
[CmdletBinding()]
param(
    [string]$SharpHoundPath = ".\SharpHound.ps1",
    [string]$OutputDir = (Join-Path (Get-Location) "vanguard-discovery"),
    [string]$ZipPath = (Join-Path (Get-Location) "vanguard-discovery.zip")
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $SharpHoundPath)) {
    throw "SharpHound.ps1 not found at $SharpHoundPath. Download from the BloodHound CE release page."
}
if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Import-Module $SharpHoundPath
Invoke-BloodHound -CollectionMethod All -OutputDirectory $OutputDir -OutputPrefix vanguard

if (Test-Path -LiteralPath $ZipPath) { Remove-Item -LiteralPath $ZipPath -Force }
Compress-Archive -Path (Join-Path $OutputDir "*") -DestinationPath $ZipPath -Force

Write-Host "Wrote $ZipPath"
Write-Host "Upload this file to the Vanguard backend (POST /api/exports)."
