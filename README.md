# Vanguard v2 — 6-Stage AD Attack-Path Defense

Matches the pipeline in the project brief:

1. **AD Discovery** — SharpHound/BloodHound CE ingestion (`Stage1-Discover.ps1` + `backend/stages/discovery.py`)
2. **Attack-Path Analysis** — NetworkX graph analyzer (`backend/stages/analysis.py`)
3. **AI Decision Engine** — Rule-based remediation selector (`backend/stages/decision.py` + `backend/rules/`)
4. **AD Remediation** — PowerShell plan generator + rollback (`backend/stages/remediation.py` + `Stage4-*.ps1`)
5. **Re-Attack & Verification** — before/after comparator + lab Impacket script (`backend/stages/verification.py` + `Stage5-ReAttack.ps1`)
6. **Backend & Dashboard** — FastAPI + SQLite + static dashboard (`backend/main.py` + `frontend/`)

## Team member mapping

| Member | Role | Where their code lives |
|--------|------|------------------------|
| 1 | Lab Builder | `scripts/Stage0-BuildLab.ps1` |
| 2 | Scanner | `scripts/Stage1-Discover.ps1`, `backend/stages/discovery.py` |
| 3 | Brain | `backend/stages/analysis.py`, `backend/stages/decision.py`, `backend/rules/` |
| 4 | Fixer | `backend/stages/remediation.py`, `scripts/Stage4-*.ps1` |
| 5 | Attacker | `scripts/Stage5-ReAttack.ps1`, `backend/stages/verification.py` |
| 6 | Dashboard | `backend/main.py`, `frontend/` |

## Run on Termux / any Linux

```bash
bash START.sh
