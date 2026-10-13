"""Stage 6 — orchestration: run Stage 1-5 in order, persist results."""
from __future__ import annotations
from datetime import datetime, timezone
from backend.db import SessionLocal
from backend import models
from backend.stages import discovery, analysis, decision, remediation, verification


def run_full_pipeline(filename: str, raw: bytes, name: str | None = None) -> dict:
    """Ingest → analyze → decide → plan. Does not apply anything."""
    db = SessionLocal()
    try:
        graph = discovery.ingest(filename, raw)
        exp = models.Export(
            name=name or filename,
            source="import",
            node_count=len(graph["nodes"]),
            edge_count=len(graph["edges"]),
            raw_json=models.dumps(graph),
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)

        run = models.Run(export_id=exp.id, status="new")
        db.add(run)
        db.commit()
        db.refresh(run)

        result = analysis.analyze(graph)

        # Persist findings
        for f in result["findings"]:
            finding = models.Finding(
                run_id=run.id,
                risk=f["risk"],
                score=f["score"],
                start_name=f["start_id"],
                target_name=f["target_id"],
                path_json=models.dumps(f["path"]),
                edges_json=models.dumps(f["edges"]),
                recommendation="Review and least-privilege the highlighted relationship.",
            )
            db.add(finding)
        db.commit()

        # Stage 3 & 4 — decisions and plan (plan written to disk for review)
        plans = remediation.generate_plan(result, out_dir="stage4_output")

        # Persist proposed actions
        for d in plans["decisions"]:
            chosen = d["chosen"]
            action = models.Action(
                run_id=run.id,
                kind=chosen["kind"],
                target=d["context"].get("target", ""),
                principal=d["context"].get("principal", ""),
                status="proposed",
                blast_radius=chosen["blast_radius"],
                pre_checks_json=models.dumps(chosen["pre_checks"]),
                rollback_json=models.dumps(chosen["rollback"]),
            )
            db.add(action)

        run.status = "analyzed"
        run.finished_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "export_id": exp.id,
            "run_id": run.id,
            "summary": {
                "node_count": result["node_count"],
                "edge_count": result["edge_count"],
                "privileged_target_count": result["privileged_target_count"],
                "start_count": result["start_count"],
                "path_count": result["path_count"],
            },
            "findings": result["findings"],
            "critical_edges": result["critical_edges"],
            "plan": {
                "apply_script": plans["apply_script"],
                "rollback_script": plans["rollback_script"],
                "action_count": plans["action_count"],
            },
            "notes": result["analysis_limits"],
        }
    finally:
        db.close()


def verify_run(before_export_id: int, after_export_id: int) -> dict:
    db = SessionLocal()
    try:
        b = db.get(models.Export, before_export_id)
        a = db.get(models.Export, after_export_id)
        if not b or not a:
            raise ValueError("Export not found")
        return verification.compare(models.loads(b.raw_json),
                                    models.loads(a.raw_json))
    finally:
        db.close()
