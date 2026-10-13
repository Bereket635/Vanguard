"""Stage 2 — Attack-Path Analysis (NetworkX).

Replaces the earlier BFS with NetworkX for: shortest simple paths, weighted
scoring, betweenness centrality, and "critical relationship" detection.
"""
from __future__ import annotations
from collections import defaultdict
import networkx as nx
from backend.rules import RISK_WEIGHTS

PRIVILEGED_HINTS = (
    "DOMAIN ADMINS", "ENTERPRISE ADMINS", "SCHEMA ADMINS",
    "ADMINISTRATORS", "DOMAIN CONTROLLERS",
    "ENTERPRISE KEY ADMINS", "KEY ADMINS", "PROTECTED USERS",
    "ACCOUNT OPERATORS", "SERVER OPERATORS", "BACKUP OPERATORS",
    "PRINT OPERATORS", "REPLICATOR", "GROUP POLICY CREATOR OWNERS",
    "KRBTGT", "ADMINSDH",
)
START_HINTS = ("USER", "SERVICEACCOUNT", "SERVICE ACCOUNT", "COMPUTER")


def _norm(v) -> str:
    return str(v or "").strip().upper().replace("_", " ")


def is_privileged(node: dict) -> bool:
    text = _norm(node.get("name")) + " " + _norm(node.get("type"))
    return any(h in text for h in PRIVILEGED_HINTS)


def is_start(node: dict) -> bool:
    t = _norm(node.get("type"))
    return any(h in t for h in START_HINTS) and not is_privileged(node)


def edge_weight(rel: str) -> float:
    key = rel.replace(" ", "").replace("_", "").replace("-", "")
    for name, weight in RISK_WEIGHTS.items():
        if name.replace("_", "") in key:
            return weight
    return 0.1


def build_digraph(graph: dict) -> nx.DiGraph:
    G = nx.DiGraph()
    for n in graph.get("nodes", []):
        G.add_node(n["id"], **n)
    for e in graph.get("edges", []):
        w = edge_weight(e.get("relationship", ""))
        G.add_edge(e["source"], e["target"],
                   relationship=e.get("relationship", "RELATED_TO"),
                   weight=w)
    return G


def find_paths(G: nx.DiGraph, start_id: str, target_ids: set[str],
               max_depth: int = 8, max_paths: int = 50) -> list[list[str]]:
    results: list[list[str]] = []
    if start_id not in G or not target_ids:
        return results
    # BFS enumerating all simple paths, depth-limited.
    queue = [(start_id, [start_id])]
    while queue and len(results) < max_paths:
        current, path = queue.pop(0)
        if current in target_ids and len(path) > 1:
            results.append(path)
            continue
        if len(path) - 1 >= max_depth:
            continue
        for nxt in G.successors(current):
            if nxt in path:
                continue
            queue.append((nxt, path + [nxt]))
    return results


def path_score(G: nx.DiGraph, path: list[str]) -> tuple[float, list[dict]]:
    """Score = sum of edge weights along path (higher = more dangerous)."""
    rels: list[dict] = []
    total = 0.0
    for a, b in zip(path, path[1:]):
        data = G.get_edge_data(a, b) or {}
        w = data.get("weight", 0.1)
        total += w
        rels.append({"source": a, "target": b,
                     "relationship": data.get("relationship", "RELATED_TO"),
                     "weight": w})
    # Shorter paths are more dangerous for the same score.
    return (total / max(1, len(path) - 1), rels)


def critical_relationships(G: nx.DiGraph, top_n: int = 10) -> list[dict]:
    """Edges that appear on the most paths to privileged targets.

    Uses edge betweenness centrality as a proxy. High centrality = choke point.
    """
    if G.number_of_edges() == 0:
        return []
    try:
        bc = nx.edge_betweenness_centrality(G)
    except Exception:
        return []
    ranked = sorted(bc.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    out = []
    for (src, tgt), score in ranked:
        data = G.get_edge_data(src, tgt) or {}
        out.append({
            "source": src, "target": tgt,
            "relationship": data.get("relationship", "RELATED_TO"),
            "centrality": round(score, 4),
        })
    return out


def analyze(graph: dict, max_depth: int = 8, max_paths: int = 50) -> dict:
    G = build_digraph(graph)
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    targets = {nid for nid, n in nodes.items() if is_privileged(n)}
    starts = [nid for nid, n in nodes.items() if is_start(n)]

    findings: list[dict] = []
    for start in starts[:500]:
        for path in find_paths(G, start, targets, max_depth, max_paths):
            score, rels = path_score(G, path)
            risky = [r for r in rels if r["weight"] >= 0.5]
            findings.append({
                "start_id": start,
                "target_id": path[-1],
                "path": path,
                "score": round(score, 3),
                "edges": rels,
                "risk": "High" if risky else "Review",
                "high_risk_edges": risky,
            })

    # Deduplicate by (start, target, path signature)
    seen = set()
    deduped = []
    for f in findings:
        sig = (f["start_id"], f["target_id"], tuple(f["path"]))
        if sig in seen:
            continue
        seen.add(sig)
        deduped.append(f)

    deduped.sort(key=lambda f: (0 if f["risk"] == "High" else 1,
                                -f["score"], len(f["path"])))

    return {
        "node_count": len(nodes),
        "edge_count": G.number_of_edges(),
        "privileged_target_count": len(targets),
        "start_count": len(starts),
        "path_count": len(deduped),
        "findings": deduped[:200],
        "critical_edges": critical_relationships(G),
        "analysis_limits": [
            "Path direction and relationship semantics depend on the export.",
            "A path is not proof of exploitability.",
            "Missing objects or stale data cause false negatives.",
            "No Active Directory changes are made by this stage.",
        ],
    }
