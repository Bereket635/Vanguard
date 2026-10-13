# Vanguard Stage 4 — generated remediation script
# Generated: 2026-10-13T05:34:05.292002+00:00
# Run only after: change approval, backup of affected SDs, and -WhatIf review.
# This script is idempotent: re-running after a successful apply is a no-op.

$ErrorActionPreference = 'Stop'
function Test-VanguardBackup {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Backup JSON not found at $Path. Run the backup step first."
    }
}


# --- Backup ----------------------------------------------------------------
$BackupPath = Join-Path $PSScriptRoot "stage4-backup.json"
$Backup = [ordered]@{
    timestamp_utc = (Get-Date).ToUniversalTime().ToString('o')
    operator      = "$env:USERDOMAIN\$env:USERNAME"
    host          = $env:COMPUTERNAME
    actions       = @()
}


# --- Action 1: remove_generic_all_ace ---

$acl = Get-Acl "AD:S-1-5-21-1000-12"
$acl.Access | Where-Object { $_.IdentityReference -like "*S-1-5-21-1000-21*" -and $_.ActiveDirectoryRights -match "GenericAll" } |
  ForEach-Object { $acl.RemoveAccessRule($_) | Out-Null }
Set-Acl "AD:S-1-5-21-1000-12" $acl

$Backup.actions += [pscustomobject]@{ index=1; kind='RemoveDaclAce'; target='S-1-5-21-1000-12'; principal='S-1-5-21-1000-21' }


# --- Action 2: remove_excess_group_membership ---

Remove-ADGroupMember -Identity "" -Members "S-1-5-21-1000-22" -Confirm:$false

$Backup.actions += [pscustomobject]@{ index=2; kind='RemoveMember'; target='S-1-5-21-1000-15'; principal='S-1-5-21-1000-22' }


# --- Action 3: remove_excess_group_membership ---

Remove-ADGroupMember -Identity "" -Members "S-1-5-21-1000-6" -Confirm:$false

$Backup.actions += [pscustomobject]@{ index=3; kind='RemoveMember'; target='S-1-5-21-1000-15'; principal='S-1-5-21-1000-6' }


# --- Action 4: remove_excess_group_membership ---

Remove-ADGroupMember -Identity "S-1-5-21-1000-10" -Members "S-1-5-21-1000-1" -Confirm:$false

$Backup.actions += [pscustomobject]@{ index=4; kind='RemoveMember'; target='S-1-5-21-1000-12'; principal='S-1-5-21-1000-1' }


# --- Action 5: remove_excess_group_membership ---

Remove-ADGroupMember -Identity "S-1-5-21-1000-10" -Members "S-1-5-21-1000-2" -Confirm:$false

$Backup.actions += [pscustomobject]@{ index=5; kind='RemoveMember'; target='S-1-5-21-1000-12'; principal='S-1-5-21-1000-2' }


# --- Action 6: remove_excess_group_membership ---

Remove-ADGroupMember -Identity "S-1-5-21-1000-11" -Members "S-1-5-21-1000-4" -Confirm:$false

$Backup.actions += [pscustomobject]@{ index=6; kind='RemoveMember'; target='S-1-5-21-1000-15'; principal='S-1-5-21-1000-4' }


# --- Action 7: remove_excess_group_membership ---

Remove-ADGroupMember -Identity "S-1-5-21-1000-11" -Members "S-1-5-21-1000-4" -Confirm:$false

$Backup.actions += [pscustomobject]@{ index=7; kind='RemoveMember'; target='S-1-5-21-1000-16'; principal='S-1-5-21-1000-4' }


# --- Action 8: remove_excess_group_membership ---

Remove-ADGroupMember -Identity "S-1-5-21-1000-14" -Members "S-1-5-21-1000-6" -Confirm:$false

$Backup.actions += [pscustomobject]@{ index=8; kind='RemoveMember'; target='S-1-5-21-1000-15'; principal='S-1-5-21-1000-6' }


# --- Action 9: remove_excess_group_membership ---

Remove-ADGroupMember -Identity "S-1-5-21-1000-13" -Members "S-1-5-21-1000-3" -Confirm:$false

$Backup.actions += [pscustomobject]@{ index=9; kind='RemoveMember'; target='S-1-5-21-1000-13'; principal='S-1-5-21-1000-3' }


# --- Action 10: remove_excess_group_membership ---

Remove-ADGroupMember -Identity "S-1-5-21-1000-15" -Members "S-1-5-21-1000-5" -Confirm:$false

$Backup.actions += [pscustomobject]@{ index=10; kind='RemoveMember'; target='S-1-5-21-1000-15'; principal='S-1-5-21-1000-5' }


# --- Action 11: remove_excess_group_membership ---

Remove-ADGroupMember -Identity "S-1-5-21-1000-16" -Members "S-1-5-21-1000-5" -Confirm:$false

$Backup.actions += [pscustomobject]@{ index=11; kind='RemoveMember'; target='S-1-5-21-1000-16'; principal='S-1-5-21-1000-5' }


# --- Action 12: remove_excess_group_membership ---

Remove-ADGroupMember -Identity "S-1-5-21-1000-15" -Members "S-1-5-21-1000-23" -Confirm:$false

$Backup.actions += [pscustomobject]@{ index=12; kind='RemoveMember'; target='S-1-5-21-1000-15'; principal='S-1-5-21-1000-23' }


$Backup | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $BackupPath -Encoding UTF8
