"""Independent reference for procmail delivery simulation (verifier only)."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Recipe:
    rid: str
    flags: str
    lock: str | None
    conditions: list[str]
    target: str | None
    children: list[Recipe] = field(default_factory=list)


def load_meta(suite: Path) -> dict[str, str]:
    data = json.loads((suite / "suite.meta.json").read_text(encoding="utf-8"))
    return {
        "HOST": str(data.get("host", "")),
        "HOSTNAME": str(data.get("hostname", "")),
        "ORGMAIL": str(data.get("orgmail", "")),
    }


def parse_mbox(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    chunks = re.split(r"(?=^From )", text, flags=re.MULTILINE)
    messages: list[dict[str, str]] = []
    for chunk in chunks:
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        lines = chunk.splitlines()
        mid = ""
        for line in lines[1:]:
            if line.lower().startswith("message-id:"):
                mid = line.split(":", 1)[1].strip().strip("<>")
                break
        if not mid:
            mid = hashlib.sha256(chunk.encode()).hexdigest()[:12]
        body = "\n".join(lines[1:])
        messages.append(
            {
                "message_id": mid,
                "raw": chunk,
                "headers": _headers_only(body),
            }
        )
    return messages


def _headers_only(text: str) -> str:
    return text.split("\n\n", 1)[0]


def _parse_flags(token: str) -> tuple[str, str | None]:
    flags = ""
    lock = None
    for part in token.split():
        if part.startswith("lock="):
            lock = part.split("=", 1)[1].strip()
        else:
            flags += part
    return flags, lock


def parse_rc(path: Path) -> tuple[dict[str, str], list[Recipe]]:
    env: dict[str, str] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    idx = 0

    def parse_block(parent: str | None, start: int) -> tuple[list[Recipe], int]:
        nonlocal env
        block: list[Recipe] = []
        local_counter = 0
        pos = start
        while pos < len(lines):
            line = lines[pos].strip()
            if not line or line.startswith("#"):
                pos += 1
                continue
            if line == "}":
                return block, pos + 1
            if line.startswith("SET "):
                _, rest = line.split(" ", 1)
                name, val = rest.split("=", 1)
                env[name.strip()] = val.strip()
                pos += 1
                continue
            if not line.startswith(":0"):
                pos += 1
                continue
            local_counter += 1
            rid = f"{parent}.{local_counter}" if parent else f"r{local_counter}"
            flags, lock = _parse_flags(line[2:].strip())
            pos += 1
            conditions: list[str] = []
            target: str | None = None
            children: list[Recipe] = []
            while pos < len(lines):
                inner = lines[pos].strip()
                if not inner or inner.startswith("#"):
                    pos += 1
                    continue
                if inner.startswith(":0") or inner == "}" or inner.startswith("SET "):
                    break
                if inner == "{":
                    pos += 1
                    children, pos = parse_block(rid, pos)
                    continue
                if inner.startswith("*"):
                    conditions.append(inner[1:].strip())
                    pos += 1
                    continue
                target = inner
                pos += 1
                break
            block.append(
                Recipe(
                    rid=rid,
                    flags=flags,
                    lock=lock,
                    conditions=conditions,
                    target=target,
                    children=children,
                )
            )
        return block, pos

    recipes, _ = parse_block(None, idx)
    return env, recipes


def _match_conditions(recipe: Recipe, msg: dict[str, str], env: dict[str, str]) -> bool:
    text = msg["headers"] if "h" in recipe.flags else msg["raw"]
    for cond in recipe.conditions:
        cond = cond.strip()
        if cond.startswith("?"):
            var = cond[1:].strip()
            if var == "$HOSTNAME":
                needle = env.get("HOSTNAME", "")
                return bool(needle) and re.search(re.escape(needle), msg["headers"]) is not None
            if var == "$HOST":
                needle = env.get("HOST", "")
                return bool(needle) and re.search(re.escape(needle), msg["headers"]) is not None
            return False
        if not re.search(cond, text, re.MULTILINE):
            return False
    return True


def _lock_path(scope: str, name: str) -> str:
    return f"/app/state/locks/{scope}/{name}"


def reference_simulate(suite: Path, held_locks: set[str] | None = None) -> dict[str, Any]:
    meta = load_meta(suite)
    rc_env, recipes = parse_rc(suite / "procmail.rc")
    env = {**meta, **rc_env}
    messages = parse_mbox(suite / "messages.mbox")

    deliveries: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    stats = {
        "messages_total": len(messages),
        "recipes_evaluated": 0,
        "recipes_skipped": 0,
        "deliveries_count": 0,
        "lock_serializations": 0,
        "orgmail_fallbacks": 0,
        "duplicate_suppressed": 0,
    }
    active_locks: set[str] = set(held_locks or ())

    def deliver(msg_id: str, mbox: str, rid: str, reason: str) -> None:
        for d in deliveries:
            if d["message_id"] == msg_id and d["mbox"] == mbox and d["recipe_id"] == rid:
                stats["duplicate_suppressed"] += 1
                return
        deliveries.append(
            {"message_id": msg_id, "mbox": mbox, "recipe_id": rid, "reason": reason}
        )
        stats["deliveries_count"] += 1
        if reason == "orgmail_fork_fallback":
            stats["orgmail_fallbacks"] += 1

    def eval_block(block: list[Recipe], msg: dict[str, str], scope: str) -> bool:
        any_delivered = False
        for recipe in block:
            stats["recipes_evaluated"] += 1
            lock_path = None
            if recipe.lock:
                lock_path = _lock_path(scope, recipe.lock)
                if lock_path in active_locks:
                    skipped.append({"recipe_id": recipe.rid, "reason": "lock_busy"})
                    stats["recipes_skipped"] += 1
                    continue
                active_locks.add(lock_path)
                stats["lock_serializations"] += 1
            try:
                if not _match_conditions(recipe, msg, env):
                    continue
                inner_delivered = False
                if recipe.children:
                    child_scope = recipe.rid if scope == "root" else f"{scope}/{recipe.rid}"
                    inner_delivered = eval_block(recipe.children, msg, child_scope)
                    if not inner_delivered and env.get("ORGMAIL"):
                        deliver(
                            msg["message_id"],
                            env["ORGMAIL"],
                            recipe.rid,
                            "orgmail_fork_fallback",
                        )
                        inner_delivered = True
                if recipe.target:
                    deliver(msg["message_id"], recipe.target, recipe.rid, "match")
                    inner_delivered = True
                if inner_delivered:
                    any_delivered = True
                    if "c" not in recipe.flags:
                        break
            finally:
                if lock_path:
                    active_locks.discard(lock_path)
        return any_delivered

    for msg in messages:
        eval_block(recipes, msg, "root")

    suite_id = json.loads((suite / "suite.meta.json").read_text(encoding="utf-8")).get(
        "suite_id", suite.name
    )
    return {
        "snapshot_version": 1,
        "suite_id": suite_id,
        "environment": {
            "HOST": env.get("HOST", ""),
            "HOSTNAME": env.get("HOSTNAME", ""),
            "ORGMAIL": env.get("ORGMAIL", ""),
        },
        "deliveries": deliveries,
        "skipped_recipes": skipped,
        "stats": stats,
    }


def reference_audit(snapshot: dict[str, Any], snapshot_bytes: bytes) -> dict[str, Any]:
    return {
        "audit_version": 1,
        "suite_id": snapshot["suite_id"],
        "environment": snapshot["environment"],
        "stats": snapshot["stats"],
        "deliveries": snapshot["deliveries"],
        "skipped_recipes": snapshot["skipped_recipes"],
        "snapshot_sha256": hashlib.sha256(snapshot_bytes).hexdigest(),
    }


def audit_from_snapshot_path(snapshot_path: Path) -> dict[str, Any]:
    """Build expected audit JSON from an on-disk delivery snapshot."""
    snapshot_bytes = snapshot_path.read_bytes()
    snapshot = json.loads(snapshot_bytes.decode("utf-8"))
    return reference_audit(snapshot, snapshot_bytes)
