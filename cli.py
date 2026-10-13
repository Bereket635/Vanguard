#!/usr/bin/env python3
"""Vanguard CLI. Drives the full 6-stage pipeline offline."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from backend.stages import discovery, analysis, decision, remediation, verification


def _load(path: Path) -> dict:
    return discovery.ingest(path.name, path.read_bytes())


def cmd_analyze(args):
    g = _load(Path(args.file))
    r = analysis.analyze(g, max_depth=args.depth, max_paths=args.max_paths)
    print(f"Nodes: {r['node_count']}  Edges: {r['edge_count']}")
    print(f"Privileged: {r['privileged_target_count']}  Starts: {r['start_count']}")
    print(f"Findings: {r['path_count']}")
    print()
    for f in r["findings"][:args.limit]:
        sig = " -> ".join(f["path"])
        print(f"[{f['risk']}] score={f['score']}  {sig}")
    return 0


def cmd_decide(args):
    g = _load(Path(args.file))
    r = analysis.analyze(g)
    plans = remediation.generate_plan(r, out_dir=args.out_dir)
    print(f"Actions proposed: {plans['action_count']}")
    print(f"Apply:    {plans['apply_script']}")
    print(f"Rollback: {plans['rollback_script']}")
    return 0


def cmd_verify(args):
    b = _load(Path(args.before))
    a = _load(Path(args.after))
    result = verification.compare(b, a)
    print(json.dumps(result, indent=2, default=str))
    return 0


def cmd_report(args):
    g = _load(Path(args.file))
    r = analysis.analyze(g)
    out = Path(args.output)
    out.write_text(json.dumps(r, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="vanguard")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze")
    a.add_argument("file"); a.add_argument("--limit", type=int, default=30)
    a.add_argument("--depth", type=int, default=8)
    a.add_argument("--max-paths", type=int, default=50)
    a.set_defaults(func=cmd_analyze)

    d = sub.add_parser("decide")
    d.add_argument("file"); d.add_argument("--out-dir", default="stage4_output")
    d.set_defaults(func=cmd_decide)

    v = sub.add_parser("verify")
    v.add_argument("before"); v.add_argument("after")
    v.set_defaults(func=cmd_verify)

    r = sub.add_parser("report")
    r.add_argument("file"); r.add_argument("-o", "--output", default="report.json")
    r.set_defaults(func=cmd_report)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
