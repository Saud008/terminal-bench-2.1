"""Independent sysctl tree merger (verifier-only)."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
VERIFIER_SEED = os.environ.get("VERIFIER_SEED", "base")


def normalize_value(raw: str) -> str:
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        inner = raw[1:-1]
        return inner.replace('\\"', '"')
    return raw


def strip_inline_comment(line: str) -> str:
    for idx, ch in enumerate(line):
        if ch == "#" and idx > 0 and line[idx - 1].isspace():
            return line[:idx].rstrip()
    return line.strip()


def parse_assignment(line: str) -> tuple[str, str] | None:
    m = re.match(r"^([a-z0-9][a-z0-9_.-]*)\s*=\s*(.+)$", line, re.IGNORECASE)
    if m:
        return m.group(1), m.group(2).strip()
    m = re.match(r"^([a-z0-9][a-z0-9_.-]*)\s+(\S.*)$", line, re.IGNORECASE)
    if m:
        return m.group(1), m.group(2).strip()
    return None


def parse_fragment(path: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = strip_inline_comment(line)
        if not line:
            continue
        parsed = parse_assignment(line)
        if not parsed:
            errors.append({"line": line_no, "reason": "malformed"})
            continue
        key, value = parsed
        if "." not in key or not KEY_RE.match(key):
            errors.append({"line": line_no, "reason": "invalid_key", "key": key})
            continue
        entries.append({"key": key, "value": value, "line": line_no})
    return {"file": str(path), "entries": entries, "errors": errors}


def drop_in_order(tree: Path, seed: str) -> list[str]:
    manifest = json.loads((tree / "manifest.json").read_text(encoding="utf-8"))
    drop_ins = list(manifest.get("drop_ins", []))
    drop_ins.sort(key=lambda rel: hashlib.sha256(f"{seed}:{rel}".encode()).hexdigest())
    return drop_ins


def reference_staging_path(snapshot: Path) -> Path:
    return snapshot.with_suffix(snapshot.suffix + ".merge-staging.json")


def snapshot_digest(meta: dict[str, Any]) -> str:
    payload = {
        "processing_order": meta["processing_order"],
        "effective": meta["effective"],
        "sources": meta["sources"],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def reference_staging(tree: Path, snapshot_meta: dict[str, Any]) -> dict[str, Any]:
    layer_keys = []
    for rel in snapshot_meta["processing_order"]:
        parsed = parse_fragment(tree / rel)
        keys: list[str] = []
        for ent in parsed["entries"]:
            if ent["key"] in keys:
                keys.remove(ent["key"])
            keys.append(ent["key"])
        layer_keys.append({"file": rel, "keys": keys})
    order = snapshot_meta["processing_order"]
    return {
        "staging_version": 1,
        "snapshot_digest": snapshot_digest(snapshot_meta),
        "layer_keys": layer_keys,
        "last_file": order[-1] if order else "",
    }


def reference_apply(tree: Path, seed: str) -> dict[str, Any]:
    manifest = json.loads((tree / "manifest.json").read_text(encoding="utf-8"))
    files: list[str] = []
    main = manifest.get("main")
    if main:
        files.append(main)
    files.extend(drop_in_order(tree, seed))

    effective: dict[str, str] = {}
    sources: dict[str, dict[str, Any]] = {}
    for rel in files:
        parsed = parse_fragment(tree / rel)
        if parsed["errors"]:
            raise ValueError(f"parse errors in {rel}: {parsed['errors']}")
        for ent in parsed["entries"]:
            effective[ent["key"]] = normalize_value(ent["value"])
            sources[ent["key"]] = {"file": rel, "line": ent["line"]}

    return {
        "apply_version": 1,
        "tree": tree.name,
        "seed": seed,
        "processing_order": files,
        "effective": effective,
        "sources": sources,
        "stats": {"keys": len(effective), "files_processed": len(files)},
        "apply_digest": snapshot_digest(
            {
                "processing_order": files,
                "effective": effective,
                "sources": sources,
            }
        ),
    }


def collision_winner(tree: Path, seed: str) -> str:
    doc = reference_apply(tree, seed)
    return doc["effective"]["shared.collision.key"]
