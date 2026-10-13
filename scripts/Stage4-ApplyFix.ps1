<#
.SYNOPSIS
    Stage 4 apply wrapper. Runs the generated plan with approval gate.
.DESCRIPTION
    This wrapper is what the operator actually runs. It refuses to run unless
    -Approved is supplied AND a backup exists.
#>
[CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='High')]
param(
    [string]$GeneratedPlan = ".\stage4_output\Stage4-ApplyFix.ps1",
    [switch]$Approved,
    [string]$BackupPath = (Join-Path $PSScriptRoot "stage4-backup.json")
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $GeneratedPlan)) {
    throw "Generated plan not found: $GeneratedPlan. Run Stage 3/4 first."
}
if (-not $Approved) {
    throw "Refusing to apply without -Approved. Review the plan first: $GeneratedPlan"
}
if (Test-Path -LiteralPath $BackupPath) {
    Write-Host "Existing backup found at $BackupPath — keeping as-is."
} else {
    New-Item -ItemType File -Path $BackupPath -Force | Out-Null
    '{"note":"Vanguard backup placeholder; overwritten by plan"}' | Set-Content -LiteralPath $BackupPath
}

Write-Host "Applying $GeneratedPlan ..."
& $GeneratedPlan
Write-Host "Apply complete. Backup at $BackupPath"
Write-Host "Now run Stage 1 again on the modified domain to verify (Stage 5)."
