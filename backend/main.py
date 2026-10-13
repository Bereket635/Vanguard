"""Vanguard backend — Flask version (Termux-friendly, no Rust deps)."""
from __future__ import annotations
import os
from pathlib import Path
from flask import Flask, request, jsonify, send_file, Response
from backend.db import init_db
from backend import models
from backend.stages import pipeline, analysis, remediation

app = Flask(__name__)
FRONTEND = Path(__file__).resolve().parent.parent / "frontend"

# Initialize DB on first request
_db_ready = False


@app.before_request
def _ensure_db():
    global _db_ready
    if not _db_ready:
        init_db()
        _db_ready = True


def _role():
    """Simple role resolver. Dev mode = admin. Set VANGUARD_API_KEYS
    to 'token:role,token:role' to enable."""
    keys_raw = os.environ.get("VANGUARD_API_KEYS", "").strip()
    if not keys_raw:
        return "admin"
    keys = dict(k.split(":", 1) for k in keys_raw.split(",") if ":" in k)
    token = request.headers.get("X-API-Key", "")
    return keys.get(token.strip(), None)


def _require(*roles):
    r = _role()
    if r is None:
        return jsonify({"error": "missing or invalid API key"}), 401
    if r not in roles:
        return jsonify({"error": f"requires one of {roles}"}), 403
    return None


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "app": "Vanguard 6-stage pipeline (Flask)",
        "live_ad_connected": False,
        "automatic_remediation_enabled": False,
    })


@app.post("/api/exports")
def create_export():
    err = _require("analyst", "fixer", "admin")
    if err:
        return err
    if "file" not in request.files:
        return jsonify({"error": "no file uploaded"}), 400
    f = request.files["file"]
    raw = f.read()
    if len(raw) > 80 * 1024 * 1024:
        return jsonify({"error": "upload exceeds 80 MB"}), 413
    try:
        return jsonify(pipeline.run_full_pipeline(
            f.filename, raw, request.form.get("name") or None))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/demo")
def create_demo():
    err = _require("analyst", "fixer", "admin")
    if err:
        return err
    import json
    from tools.make_demo_export import build_graph
    graph = build_graph(seed=7, size="medium")
    raw = json.dumps(graph).encode("utf-8")
    try:
        return jsonify(pipeline.run_full_pipeline("demo.json", raw, "Synthetic demo"))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/exports/<int:export_id>")
def get_export(export_id):
    err = _require("reader", "analyst", "fixer", "admin")
    if err:
        return err
    from backend.db import SessionLocal
    db = SessionLocal()
    try:
        exp = db.get(models.Export, export_id)
        if not exp:
            return jsonify({"error": "export not found"}), 404
        return jsonify({
            "id": exp.id, "name": exp.name, "source": exp.source,
            "node_count": exp.node_count, "edge_count": exp.edge_count,
        })
    finally:
        db.close()


@app.get("/api/runs/<int:run_id>/findings")
def run_findings(run_id):
    err = _require("reader", "analyst", "fixer", "admin")
    if err:
        return err
    from backend.db import SessionLocal
    db = SessionLocal()
    try:
        rows = db.query(models.Finding).filter_by(run_id=run_id).all()
        return jsonify([{
            "id": r.id, "risk": r.risk, "score": r.score,
            "start": r.start_name, "target": r.target_name,
            "path": models.loads(r.path_json),
            "edges": models.loads(r.edges_json),
        } for r in rows])
    finally:
        db.close()


@app.post("/api/runs/<int:run_id>/plan")
def plan(run_id):
    err = _require("fixer", "admin")
    if err:
        return err
    from backend.db import SessionLocal
    db = SessionLocal()
    try:
        run = db.get(models.Run, run_id)
        if not run:
            return jsonify({"error": "run not found"}), 404
        graph = models.loads(run.export.raw_json)
        result = analysis.analyze(graph)
        plans = remediation.generate_plan(result, out_dir=f"stage4_output/run_{run_id}")
        return jsonify({
            "apply_script": plans["apply_script"],
            "rollback_script": plans["rollback_script"],
            "action_count": plans["action_count"],
        })
    finally:
        db.close()


@app.get("/api/verify")
def verify():
    err = _require("analyst", "fixer", "admin")
    if err:
        return err
    b = request.args.get("before", type=int)
    a = request.args.get("after", type=int)
    if not b or not a:
        return jsonify({"error": "before and after export ids required"}), 400
    try:
        return jsonify(pipeline.verify_run(b, a))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/")
def index():
    return send_file(FRONTEND / "index.html")


@app.get("/static/<path:filename>")
def static_file(filename):
    return send_file(FRONTEND / filename)


def run():
    app.run(host="127.0.0.1", port=8000, debug=False)


if __name__ == "__main__":
    run()
