"""Independent reference for paramgate OpenAPI parameter policy binding."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

import yaml

APP = Path("/app")
BASE_SPEC = APP / "fixtures/openapi-base.yaml"
ADMIN_SPEC = APP / "fixtures/admin-paths.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def merge_specs() -> dict[str, Any]:
    base = _load_yaml(BASE_SPEC)
    admin = _load_yaml(ADMIN_SPEC)
    paths = dict(base.get("paths", {}))
    paths.update(admin.get("paths", {}))
    base["paths"] = paths
    return base


def _explode_default(style: str) -> bool:
    if style == "deepObject":
        return True
    if style == "form":
        return False
    return False


def _explode(param: dict[str, Any]) -> bool:
    if "explode" in param:
        return bool(param["explode"])
    style = param.get("style") or "form"
    return _explode_default(style)


def _parse_query_array(vals: list[str], style: str, explode: bool) -> list[str]:
    if style == "form" and explode:
        return [v for v in vals if v != ""]
    joined = ",".join(vals)
    parts = [p.strip() for p in joined.split(",")]
    return [p for p in parts if p]


def _parse_query_object(q: dict[str, list[str]], name: str, style: str, explode: bool) -> dict[str, str]:
    out: dict[str, str] = {}
    if style == "deepObject" and explode:
        prefix = f"{name}["
        for key, vals in q.items():
            if key.startswith(prefix) and key.endswith("]"):
                field = key[len(prefix) : -1]
                if vals:
                    out[field] = vals[0]
        return out
    raw_vals = q.get(name, [])
    if not raw_vals or raw_vals[0] == "":
        return out
    for pair in raw_vals[0].split(","):
        if "=" in pair:
            k, v = pair.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def _parse_date(raw: str) -> str:
    if len(raw) == 10 and raw[4] == "-":
        return date.fromisoformat(raw).isoformat()
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


def _canonicalize(params: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in sorted(params):
        val = params[key]
        if isinstance(val, dict):
            out[key] = {k: val[k] for k in sorted(val)}
        else:
            out[key] = val
    return out


def bind_get(path: str, query: str) -> dict[str, Any]:
    spec = merge_specs()
    op = spec["paths"][path]["get"]
    q = parse_qs(query, keep_blank_values=True)
    params: dict[str, Any] = {}
    route_segs = [s for s in path.strip("/").split("/") if s]
    req_segs = [s for s in path.strip("/").split("/") if s]
    for i, seg in enumerate(route_segs):
        if seg.startswith("{") and seg.endswith("}"):
            name = seg[1:-1]
            params[name] = req_segs[i]
    for p in op.get("parameters", []):
        if p["in"] != "query":
            continue
        style = p.get("style") or "form"
        explode = _explode(p)
        name = p["name"]
        schema = p.get("schema", {})
        if schema.get("type") == "object":
            parsed = _parse_query_object(q, name, style, explode)
            if parsed:
                params[name] = parsed
            continue
        vals = q.get(name, [])
        if not vals or (len(vals) == 1 and vals[0] == ""):
            continue
        if schema.get("type") == "array":
            params[name] = _parse_query_array(vals, style, explode)
        elif schema.get("format") == "date":
            params[name] = _parse_date(vals[0])
        else:
            params[name] = vals[0]
    return _canonicalize(params)


def expected_snapshot(method: str, route: str, query: str, bind_seq: int = 1) -> dict[str, Any]:
    params = bind_get(route, query) if method == "GET" else {}
    return {
        "bind_seq": bind_seq,
        "method": method,
        "route": route,
        "params": params,
    }


def expected_success_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {"status": "ok", "params": snapshot["params"]}
    if snapshot.get("body"):
        payload["body"] = snapshot["body"]
    return payload
