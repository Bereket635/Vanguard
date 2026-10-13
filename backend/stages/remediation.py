"""Stage 4 — AD Remediation.

Generates a PowerShell apply script and a matching rollback script for each
approved decision. Never runs anything itself — the operator runs the script
on a domain-joined host after review. This keeps the fix surface auditable.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from backend.stages.decision import decide
from backend.stages.analysis import build_digraph


HEADER = """# Vanguard Stage 4 — generated remediation script
# Generated: {ts}
# Run only after: change approval, backup of affected SDs, and -WhatIf review.
# This script is idempotent: re-running after a successful apply is a no-op.

$ErrorActionPreference = 'Stop'
function Test-VanguardBackup {{
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {{
        throw "Backup JSON not found at $Path. Run the backup step first."
    }}
}}
"""


def _backup_block(ctx: dict) -> str:
    return f"""
# --- Backup ----------------------------------------------------------------
$BackupPath = Join-Path $PSScriptRoot "stage4-backup.json"
$Backup = [ordered]@{{
    timestamp_utc = (Get-Date).ToUniversalTime().ToString('o')
    operator      = "$env:USERDOMAIN\\$env:USERNAME"
    host          = $env:COMPUTERNAME
    actions       = @()
}}
"""


def _ps_for_action(action: dict, ctx: dict) -> str:
    apply = action.get("ps_apply", "").strip()
    if not apply:
        return f"# No apply step generated for {action.get('kind')}\n"
    for k, v in ctx.items():
        apply = apply.replace(f"<{k}>", str(v or ""))
    return apply + "\n"


def _ps_rollback_for_action(action: dict, ctx: dict) -> str:
    rb = action.get("ps_rollback", "").strip()
    if not rb:
        return f"# No rollback generated for {action.get('kind')}\n"
    for k, v in ctx.items():
        rb = rb.replace(f"<{k}>", str(v or ""))
    return rb + "\n"


def _context_from_finding(finding: dict, decision: dict) -> dict:
    """Extract template variables <group>, <principal>, <target_dn>, etc."""
    path = finding.get("path", [])
    rels = finding.get("edges", [])
    ctx = {
        "principal": "", "group": "", "target": "", "target_dn": "",
    }
    if len(path) >= 2 and rels:
        first = rels[0]
        ctx["principal"] = first.get("source", path[0])
        if "MemberOf" in first.get("relationship", ""):
            ctx["group"] = first.get("target", path[1])
        last = rels[-1]
        ctx["target"] = last.get("target", path[-1])
        ctx["target_dn"] = ctx["target"]  # placeholder; DNS resolved in PS
    return ctx


def generate_plan(analysis: dict, out_dir: str | Path) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    decisions = []
    for finding in analysis.get("findings", []):
        d = decide(finding)
        if d["chosen"]:
            d["context"] = _context_from_finding(finding, d)
            decisions.append(d)

    ts = datetime.now(timezone.utc).isoformat()
    apply_lines = [HEADER.format(ts=ts), _backup_block({})]
    rollback_lines = [HEADER.format(ts=ts), _backup_block({})]

    for i, d in enumerate(decisions):
        ctx = d["context"]
        apply_lines.append(f"\n# --- Action {i+1}: {d['chosen']['fix_id']} ---\n")
        apply_lines.append(_ps_for_action(d["chosen"], ctx))
        apply_lines.append(
            f"$Backup.actions += [pscustomobject]@{{ "
            f"index={i+1}; kind='{d['chosen']['kind']}'; "
            f"target='{ctx.get('target','')}'; principal='{ctx.get('principal','')}' }}\n"
        )
        rollback_lines.append(f"\n# --- Rollback {i+1}: {d['chosen']['fix_id']} ---\n")
        rollback_lines.append(_ps_rollback_for_action(d["chosen"], ctx))

    apply_lines.append('\n$Backup | ConvertTo-Json -Depth 6 | '
                       'Set-Content -LiteralPath $BackupPath -Encoding UTF8\n')
    rollback_lines.append('\n$Backup | ConvertTo-Json -Depth 6 | '
                          'Set-Content -LiteralPath $BackupPath -Encoding UTF8\n')

    apply_path = out / "Stage4-ApplyFix.ps1"
    rollback_path = out / "Stage4-RollbackFix.ps1"
    apply_path.write_text("\n".join(apply_lines), encoding="utf-8")
    rollback_path.write_text("\n".join(rollback_lines), encoding="utf-8")

    return {
        "apply_script": str(apply_path),
        "rollback_script": str(rollback_path),
        "action_count": len(decisions),
        "decisions": decisions,
    }
