"""Minimal API-key auth. Reads VANGUARD_API_KEYS as comma-separated tokens.

Roles:
    reader  -> GET endpoints
    analyst -> reader + analyze
    fixer   -> analyst + apply
    admin   -> everything, including rollback

If VANGUARD_API_KEYS is unset, auth is disabled (local dev only).
"""
from __future__ import annotations
import os
from fastapi import Header, HTTPException, Depends

_RAW = os.environ.get("VANGUARD_API_KEYS", "").strip()
# Format: token:role,token:role
_KEYS: dict[str, str] = {}
if _RAW:
    for entry in _RAW.split(","):
        if ":" in entry:
            tok, role = entry.split(":", 1)
            _KEYS[tok.strip()] = role.strip()


def current_role(x_api_key: str = Header(default="")) -> str:
    if not _KEYS:
        return "admin"          # dev mode
    role = _KEYS.get(x_api_key)
    if not role:
        raise HTTPException(status_code=401, detail="Missing or invalid API key")
    return role


def require(*roles: str):
    def _dep(role: str = Depends(current_role)) -> str:
        if role not in roles:
            raise HTTPException(status_code=403, detail=f"Requires one of: {roles}")
        return role
    return _dep
