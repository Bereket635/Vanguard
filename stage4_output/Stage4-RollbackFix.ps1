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


# --- Rollback 1: remove_generic_all_ace ---

# Restore from Stage 4 backup JSON captured at apply time.


# --- Rollback 2: remove_excess_group_membership ---

Add-ADGroupMember -Identity "" -Members "S-1-5-21-1000-22"


# --- Rollback 3: remove_excess_group_membership ---

Add-ADGroupMember -Identity "" -Members "S-1-5-21-1000-6"


# --- Rollback 4: remove_excess_group_membership ---

Add-ADGroupMember -Identity "S-1-5-21-1000-10" -Members "S-1-5-21-1000-1"


# --- Rollback 5: remove_excess_group_membership ---

Add-ADGroupMember -Identity "S-1-5-21-1000-10" -Members "S-1-5-21-1000-2"


# --- Rollback 6: remove_excess_group_membership ---

Add-ADGroupMember -Identity "S-1-5-21-1000-11" -Members "S-1-5-21-1000-4"


# --- Rollback 7: remove_excess_group_membership ---

Add-ADGroupMember -Identity "S-1-5-21-1000-11" -Members "S-1-5-21-1000-4"


# --- Rollback 8: remove_excess_group_membership ---

Add-ADGroupMember -Identity "S-1-5-21-1000-14" -Members "S-1-5-21-1000-6"


# --- Rollback 9: remove_excess_group_membership ---

Add-ADGroupMember -Identity "S-1-5-21-1000-13" -Members "S-1-5-21-1000-3"


# --- Rollback 10: remove_excess_group_membership ---

Add-ADGroupMember -Identity "S-1-5-21-1000-15" -Members "S-1-5-21-1000-5"


# --- Rollback 11: remove_excess_group_membership ---

Add-ADGroupMember -Identity "S-1-5-21-1000-16" -Members "S-1-5-21-1000-5"


# --- Rollback 12: remove_excess_group_membership ---

Add-ADGroupMember -Identity "S-1-5-21-1000-15" -Members "S-1-5-21-1000-23"


$Backup | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $BackupPath -Encoding UTF8
