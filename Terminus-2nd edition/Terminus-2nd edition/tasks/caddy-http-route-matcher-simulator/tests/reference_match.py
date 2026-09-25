"""Independent reference matcher for caddyctl route simulation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _fold(s: str) -> str:
    return s.lower()


def _parse_http(data: bytes) -> dict[str, Any]:
    lines = data.decode("utf-8").splitlines()
    if not lines:
        raise ValueError("empty request")
    parts = lines[0].split()
    method, path = parts[0], parts[1]
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if not line:
            break
        name, val = line.split(":", 1)
        headers[_fold(name.strip())] = val.strip()
    return {"method": method, "path": path, "headers": headers}


def _path_prefix(pattern: str, path: str) -> bool:
    if pattern.endswith("*"):
        return path.startswith(pattern[:-1])
    return pattern == path


def _path_regexp(pattern: str, path: str) -> bool:
    pat = pattern
    if not pat.startswith("^"):
        pat = "^" + pat
    if not pat.endswith("$"):
        pat = pat + "$"
    return re.match(pat, path) is not None


def _block_matches(block: dict, req: dict) -> bool:
    if methods := block.get("method"):
        if req["method"] not in methods:
            return False
    if paths := block.get("path"):
        if not any(_path_prefix(p, req["path"]) for p in paths):
            return False
    if regexps := block.get("path_regexp"):
        if not any(_path_regexp(p, req["path"]) for p in regexps):
            return False
    if headers := block.get("header"):
        for name, want_vals in headers.items():
            actual = req["headers"].get(_fold(name), "")
            folded_vals = [_fold(w) for w in want_vals]
            if _fold(actual) not in folded_vals:
                return False
    return True


def _route_matches(route: dict, req: dict) -> bool:
    matchers = route.get("matchers") or []
    if not matchers:
        return False
    return all(_block_matches(b, req) for b in matchers)


def _score(route: dict) -> int:
    score = 0
    for block in route.get("matchers") or []:
        for p in block.get("path") or []:
            score += 10 if p.endswith("*") else 30
        score += 20 * len(block.get("path_regexp") or [])
        score += 15 * len(block.get("header") or {})
        score += 5 * len(block.get("method") or [])
    return score


def _group_winner(routes: list[dict], req: dict) -> dict | None:
    by_group: dict[str, list[dict]] = {}
    for r in routes:
        if _route_matches(r, req):
            by_group.setdefault(r["group"], []).append(r)
    if not by_group:
        return None
    group = sorted(by_group.keys())[0]
    candidates = sorted(by_group[group], key=lambda r: r["index"])
    filtered: list[dict] = []
    for r in candidates:
        if r.get("handle_path"):
            continue
        filtered.append(r)
        if r.get("terminal"):
            break
    if not filtered:
        for r in candidates:
            if r.get("handle_path"):
                filtered.append(r)
    if not filtered:
        return None
    filtered.sort(key=lambda r: (-_score(r), r["index"]))
    return filtered[0]


def reference_handler_id(stage_path: Path, request_bytes: bytes) -> str | None:
    stage = json.loads(stage_path.read_text(encoding="utf-8"))
    req = _parse_http(request_bytes)
    winner = _group_winner(stage["routes"], req)
    if winner is None:
        return None
    return winner["handler_id"]


def reference_export_doc(stage_path: Path, commit_path: Path, handler_id: str) -> dict:
    commit = json.loads(commit_path.read_text(encoding="utf-8"))
    return {"handler_id": handler_id, "replay_seq": commit["replay_seq"]}
