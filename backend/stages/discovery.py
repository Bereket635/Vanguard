"""Stage 1 — AD Discovery.

Ingests a Vanguard JSON, BloodHound/SharpHound JSON, or ZIP export and
normalizes it into the Vanguard graph schema. In a lab with BloodHound CE
running, scripts/Stage1-Discover.ps1 generates the ZIP; this module consumes it.
"""
from __future__ import annotations
import io, json, zipfile
from pathlib import PurePosixPath
from typing import Any


def _node_id(item: dict) -> str | None:
    for k in ("id", "objectid", "ObjectIdentifier", "sid", "SID", "guid", "GUID"):
        v = item.get(k)
        if v and str(v).strip():
            return str(v).strip()
    for k in ("name", "Name", "samaccountname", "SamAccountName"):
        v = item.get(k)
        if v:
            return str(v).strip()
    return None


def _node_name(item: dict) -> str:
    for k in ("name", "Name", "displayname", "DisplayName",
              "samaccountname", "SamAccountName", "label"):
        v = item.get(k)
        if v:
            return str(v).strip()
    return _node_id(item) or "Unknown"


def _node_type(item: dict, fallback="Unknown") -> str:
    for k in ("type", "kind", "objecttype", "ObjectType", "label"):
        v = item.get(k)
        if v and str(v).lower() != "node":
            return str(v).strip()
    return fallback


def _edge_endpoints(e: dict) -> tuple[str | None, str | None]:
    src = tgt = None
    for k in ("source", "start", "from", "src", "StartNode", "startNode"):
        if k in e:
            v = e[k]
            src = v.get("id") if isinstance(v, dict) else v
            if src is not None:
                break
    for k in ("target", "end", "to", "dst", "EndNode", "endNode"):
        if k in e:
            v = e[k]
            tgt = v.get("id") if isinstance(v, dict) else v
            if tgt is not None:
                break
    return (str(src) if src is not None else None,
            str(tgt) if tgt is not None else None)


def _rel_name(e: dict) -> str:
    for k in ("relationship", "label", "kind", "type", "edge_type", "EdgeType"):
        if e.get(k):
            return str(e[k]).strip()
    return "RELATED_TO"


class GraphBuilder:
    def __init__(self):
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []
        self._seen_edges: set[tuple] = set()
        self.notes: list[str] = []

    def add_node(self, item: dict, fallback_type="Unknown"):
        nid = _node_id(item)
        if not nid:
            return None
        if nid not in self.nodes:
            self.nodes[nid] = {
                "id": nid, "name": _node_name(item),
                "type": _node_type(item, fallback_type), "label": _node_name(item),
            }
        elif self.nodes[nid]["type"] == "Unknown" and fallback_type != "Unknown":
            self.nodes[nid]["type"] = fallback_type
        return nid

    def add_edge(self, src: str, tgt: str, rel: str):
        if not src or not tgt or src == tgt:
            return
        key = (src, tgt, rel)
        if key in self._seen_edges:
            return
        self._seen_edges.add(key)
        self.edges.append({"source": src, "target": tgt, "relationship": rel})

    def finalize(self) -> dict:
        ids = set(self.nodes.keys())
        for e in self.edges:
            for missing in (e["source"], e["target"]):
                if missing not in ids:
                    self.nodes[missing] = {
                        "id": missing, "name": missing,
                        "type": "Unknown", "label": missing,
                    }
                    ids.add(missing)
        return {"nodes": list(self.nodes.values()),
                "edges": self.edges,
                "notes": self.notes}


def _consume(builder: GraphBuilder, obj: Any, fname: str):
    if isinstance(obj, dict) and "nodes" in obj and "edges" in obj:
        for n in obj["nodes"]:
            builder.add_node(n)
        for e in obj["edges"]:
            if isinstance(e, dict):
                s, t = _edge_endpoints(e)
                if s and t:
                    builder.add_edge(s, t, _rel_name(e))
        for note in (obj.get("notes") or []):
            builder.notes.append(str(note))
        return
    if isinstance(obj, list):
        for item in obj:
            if not isinstance(item, dict):
                continue
            props = item.get("Properties") or {}
            merged = {**props, **{k: v for k, v in item.items() if k != "Properties"}}
            sid = builder.add_node(merged, PurePosixPath(fname).stem.title())
            if not sid:
                continue
            for field in ("Members", "Aces", "Links"):
                for rel in (item.get(field) or []):
                    if isinstance(rel, dict):
                        t = _node_id(rel) or rel.get("ObjectIdentifier") or rel.get("MemberId")
                        if t:
                            builder.add_edge(sid, str(t), _rel_name(rel))
        return
    if isinstance(obj, dict) and isinstance(obj.get("data"), list):
        for item in obj["data"]:
            if not isinstance(item, dict):
                continue
            props = item.get("Properties") or {}
            merged = {**props, **{k: v for k, v in item.items() if k != "Properties"}}
            sid = builder.add_node(merged, PurePosixPath(fname).stem.title())
            if not sid:
                continue
            for field in ("Members", "Aces", "Links"):
                for rel in (item.get(field) or []):
                    if isinstance(rel, dict):
                        t = _node_id(rel) or rel.get("ObjectIdentifier") or rel.get("MemberId")
                        if t:
                            builder.add_edge(sid, str(t), _rel_name(rel))
        return
    builder.notes.append(f"Unrecognized JSON root in {fname}")


def ingest(filename: str, raw: bytes) -> dict:
    b = GraphBuilder()
    suffix = PurePosixPath(filename).suffix.lower()
    if suffix == ".zip":
        try:
            zf = zipfile.ZipFile(io.BytesIO(raw))
        except zipfile.BadZipFile as exc:
            raise ValueError(f"Invalid ZIP: {exc}")
        jsons = [i for i in zf.infolist()
                 if not i.is_dir() and i.filename.lower().endswith(".json")]
        if not jsons:
            raise ValueError("ZIP contains no JSON files")
        total = 0
        for info in jsons:
            total += info.file_size
            if total > 80 * 1024 * 1024:
                raise ValueError("Expanded ZIP > 80 MB")
            if ".." in PurePosixPath(info.filename).parts:
                b.notes.append(f"Skipped unsafe path: {info.filename}")
                continue
            try:
                obj = json.loads(zf.read(info).decode("utf-8-sig"))
            except Exception:
                b.notes.append(f"Could not parse {info.filename}")
                continue
            _consume(b, obj, info.filename)
    elif suffix == ".json":
        obj = json.loads(raw.decode("utf-8-sig"))
        _consume(b, obj, filename)
    else:
        raise ValueError("Only .json and .zip are accepted")
    graph = b.finalize()
    if not graph["nodes"]:
        raise ValueError("No nodes recognized")
    return graph
