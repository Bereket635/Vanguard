"""Stage 3 — AI Decision Engine (rule-based).

Given a finding, propose the cheapest, least-disruptive fix that removes the
path. Deterministic and auditable. The scorer is pluggable: replace
`rank_fixes` with an LLM later, keeping the same contract.
"""
from __future__ import annotations
from backend.rules import FIXES, BLAST_RADIUS, RISK_WEIGHTS


def _match_relationship(rule_rel: str, finding_rels: list[str]) -> bool:
    if rule_rel == "*":
        return True
    key = rule_rel.replace(" ", "").replace("_", "").lower()
    return any(key in r.replace(" ", "").replace("_", "").lower()
               for r in finding_rels)


def _finding_relationship_names(finding: dict) -> list[str]:
    return [e.get("relationship", "") for e in finding.get("edges", [])]


def _resolve_template(text: str, ctx: dict) -> str:
    for k, v in ctx.items():
        text = text.replace(f"<{k}>", str(v or ""))
    return text


def propose_fixes(finding: dict) -> list[dict]:
    """Return a ranked list of candidate fixes for one finding."""
    rels = _finding_relationship_names(finding)
    # Higher score = more dangerous finding.
    risk_score = finding.get("score", 0.0)
    candidates = []
    for fix in FIXES:
        if not _match_relationship(fix["matches_relationship"], rels):
            continue
        if finding.get("risk") not in fix.get("matches_risk", []):
            continue
        blast = fix.get("blast_radius", "medium")
        blast_cost = BLAST_RADIUS.get(blast, 3)
        # Combined score: prefer fixes that remove high-weight edges, with
        # low disruption.
        eff = risk_score / max(1, blast_cost)
        candidates.append({
            "fix_id": fix["id"],
            "kind": fix["kind"],
            "description": fix["description"],
            "blast_radius": blast,
            "blast_cost": blast_cost,
            "effectiveness": round(eff, 3),
            "pre_checks": fix.get("pre_checks", []),
            "rollback": fix.get("rollback", []),
            "ps_apply": fix.get("ps_apply", ""),
            "ps_rollback": fix.get("ps_rollback", ""),
        })
    candidates.sort(key=lambda c: c["effectiveness"], reverse=True)
    return candidates


def decide(finding: dict, context: dict | None = None) -> dict:
    """Pick the top fix and return a decision record."""
    ctx = context or {}
    candidates = propose_fixes(finding)
    if not candidates:
        return {
            "finding": finding.get("path", []),
            "chosen": None,
            "alternatives": [],
            "rationale": "No rule matched; manual review required.",
        }
    chosen = candidates[0]
    return {
        "finding": finding.get("path", []),
        "start": finding.get("start_id"),
        "target": finding.get("target_id"),
        "chosen": chosen,
        "alternatives": candidates[1:],
        "rationale": (
            f"Chose '{chosen['fix_id']}' (blast radius: {chosen['blast_radius']}) "
            f"with effectiveness {chosen['effectiveness']}. "
            f"Alternatives ranked lower on cost/effectiveness."
        ),
        "context": ctx,
    }


def decide_batch(analysis: dict, context: dict | None = None) -> list[dict]:
    return [decide(f, context) for f in analysis.get("findings", [])]
