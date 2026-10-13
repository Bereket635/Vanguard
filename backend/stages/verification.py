"""Stage 5 — Re-Attack & Verification.

Compares a before/after pair of analyses and proves (or disproves) that the
target paths are gone and no *alternative* path was created.
"""
from __future__ import annotations
from backend.stages.analysis import analyze


def _path_sig(f: dict) -> tuple:
    return (f["start_id"], f["target_id"], tuple(f["path"]))


def _paths_set(analysis: dict) -> set[tuple]:
    return {_path_sig(f) for f in analysis.get("findings", [])}


def compare(before_graph: dict, after_graph: dict) -> dict:
    before = analyze(before_graph)
    after = analyze(after_graph)

    b_set = _paths_set(before)
    a_set = _paths_set(after)

    removed = b_set - a_set
    added = a_set - b_set
    still_present = b_set & a_set

    def describe(path_set: set[tuple], source_analysis: dict) -> list[dict]:
        by_sig = {_path_sig(f): f for f in source_analysis["findings"]}
        out = []
        for sig in path_set:
            f = by_sig.get(sig)
            if not f:
                continue
            out.append({
                "start": f["start_id"],
                "target": f["target_id"],
                "path": f["path"],
                "risk": f["risk"],
            })
        return out

    verdict = "fixed"
    if added:
        verdict = "regressed"           # a fix created a new path
    elif still_present:
        verdict = "partial"             # some paths remain

    return {
        "verdict": verdict,
        "before": {
            "path_count": before["path_count"],
            "privileged_target_count": before["privileged_target_count"],
        },
        "after": {
            "path_count": after["path_count"],
            "privileged_target_count": after["privileged_target_count"],
        },
        "removed_paths": describe(removed, before),
        "still_present_paths": describe(still_present, after),
        "added_paths": describe(added, after),
        "notes": [
            "Verification is graph-based: it proves the modeled path is gone.",
            "It does not run live exploitation. See scripts/Stage5-ReAttack.ps1",
            "for an optional lab-only Impacket-based check.",
        ],
    }
