from __future__ import annotations
from pathlib import Path
import yaml

_RULES_PATH = Path(__file__).resolve().parent / "remediation_rules.yaml"
with _RULES_PATH.open("r", encoding="utf-8") as fh:
    RULES = yaml.safe_load(fh)

RISK_WEIGHTS = RULES["risk_weights"]
BLAST_RADIUS = RULES["blast_radius"]
FIXES = RULES["fixes"]
