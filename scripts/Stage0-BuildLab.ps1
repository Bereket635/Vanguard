<#
.SYNOPSIS
    Build a disposable AD lab for Vanguard testing.
.DESCRIPTION
    Creates ~20 users, 6 groups, and intentionally misconfigures a few
    permissions so the analyzer finds real paths.
.NOTES
    Run on a Windows Server VM you own, after promoting it to a domain.
#>
[CmdletBinding()]
param(
    [string]$DomainDn = (Get-ADDomain).DistinguishedName,
    [string]$OuName = "VanguardLab"
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Import-Module ActiveDirectory

$ouDn = "OU=$OuName,$DomainDn"
if (-not (Get-ADOrganizationalUnit -Filter "Name -eq '$OuName'" -ErrorAction SilentlyContinue)) {
    New-ADOrganizationalUnit -Name $OuName -Path $DomainDn -ProtectedFromAccidentalDeletion $false
}

$pw = ConvertTo-SecureString "ChangeMe!2024" -AsPlainText -Force
foreach ($name in @("alice.contractor","bob.helpdesk","carol.svc.backup",
                    "dave.intern","dana.admin","eve.svc.sql")) {
    if (-not (Get-ADUser -Filter "SamAccountName -eq '$name'" -ErrorAction SilentlyContinue)) {
        New-ADUser -Name $name -SamAccountName $name -Path $ouDn `
                   -AccountPassword $pw -Enabled $true -PasswordNeverExpires $true
    }
}

# Groups
foreach ($g in @("Helpdesk","IT Admins","Server Operators",
                 "Backup Operators","SQL Admins")) {
    if (-not (Get-ADGroup -Filter "Name -eq '$g'" -ErrorAction SilentlyContinue)) {
        New-ADGroup -Name $g -GroupScope Global -Path $ouDn
    }
}

# Baseline memberships
Add-ADGroupMember -Identity "Helpdesk"        -Members "alice.contractor","bob.helpdesk"
Add-ADGroupMember -Identity "IT Admins"       -Members "dave.intern"
Add-ADGroupMember -Identity "Backup Operators"-Members "carol.svc.backup"
Add-ADGroupMember -Identity "SQL Admins"      -Members "eve.svc.sql"

Write-Host "Lab users/groups created under $ouDn"
Write-Host "Manually misconfigure 2-3 ACLs (e.g. Grant GenericAll on Domain Admins to IT Admins)"
Write-Host "so the analyzer finds real paths, then re-run Stage 1."
