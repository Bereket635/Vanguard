"""ORM models and dataclass schemas. No pydantic dependency."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.db import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Export(Base):
    __tablename__ = "exports"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    source = Column(String(64), default="import")
    node_count = Column(Integer, default=0)
    edge_count = Column(Integer, default=0)
    raw_json = Column(Text, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=_utcnow)
    runs = relationship("Run", back_populates="export", cascade="all, delete-orphan")


class Run(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True)
    export_id = Column(Integer, ForeignKey("exports.id"), nullable=False)
    status = Column(String(32), default="new")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, default="")
    export = relationship("Export", back_populates="runs")
    findings = relationship("Finding", back_populates="run", cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="run", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    risk = Column(String(16))
    score = Column(Float, default=0.0)
    start_name = Column(String(255))
    target_name = Column(String(255))
    path_json = Column(Text)
    edges_json = Column(Text)
    recommendation = Column(Text, default="")
    run = relationship("Run", back_populates="findings")


class Action(Base):
    __tablename__ = "actions"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    finding_id = Column(Integer, ForeignKey("findings.id"), nullable=True)
    kind = Column(String(64))
    target = Column(String(255))
    principal = Column(String(255))
    status = Column(String(32), default="proposed")
    blast_radius = Column(String(16), default="low")
    pre_checks_json = Column(Text, default="[]")
    rollback_json = Column(Text, default="[]")
    applied_at = Column(DateTime(timezone=True), nullable=True)
    log = Column(Text, default="")
    run = relationship("Run", back_populates="actions")


# Dataclass schemas (used only for documentation; Flask returns dicts directly)
@dataclass
class ExportIn:
    name: str
    source: str = "import"
    graph: dict = field(default_factory=dict)


def dumps(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"))


def loads(text: str) -> Any:
    if not text:
        return []
    return json.loads(text)
