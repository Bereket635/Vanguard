<#
.SYNOPSIS
    Stage 4 rollback wrapper. Reverts the applied fixes.
#>
[CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='High')]
param(
    [string]$GeneratedRollback = ".\stage4_output\Stage4-RollbackFix.ps1",
    [switch]$Approved
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $GeneratedRollback)) {
    throw "Rollback script not found: $GeneratedRollback"
}
if (-not $Approved) {
    throw "Refusing to roll back without -Approved."
}
Write-Host "Rolling back via $GeneratedRollback ..."
& $GeneratedRollback
Write-Host "Rollback complete."
