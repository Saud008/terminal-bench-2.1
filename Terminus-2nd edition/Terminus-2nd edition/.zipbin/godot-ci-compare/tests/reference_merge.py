"""Independent reference Godot tscn merge exporter."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path

UID_RE = re.compile(r'uid="(uid://[^"]+)"')


def load_seeds_config(fixtures_root: Path) -> dict:
    return json.loads((fixtures_root / "seeds.json").read_text(encoding="utf-8"))


def build_remap(tree: Path, seed: int, fixtures_root: Path) -> dict[str, str]:
    seeds_cfg = load_seeds_config(fixtures_root)
    remap = json.loads((tree / "remap.json").read_text(encoding="utf-8"))
    slot = seeds_cfg.get("remap_slot")
    prefix = seeds_cfg.get("remap_prefix", "uid://player_new")
    suffix_mod = int(seeds_cfg.get("remap_suffix_mod", 5))
    if slot:
        remap[slot] = f"{prefix}_{seed % suffix_mod}"
    return remap


def normalize_lf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def apply_remap(text: str, remap: dict[str, str]) -> str:
    for old, new in sorted(remap.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(f'uid="{old}"', f'uid="{new}"')
    return text


def read_branch(tree: Path, branch: str, rel: str) -> str:
    path = tree / branch / rel
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def merge_three_way(base: str, left: str, right: str, base_name: str) -> str:
    if left == base and right == base:
        return base
    if left == base:
        return right
    if right == base:
        return left
    if left == right:
        return left
    return base


def _is_packed_scene_ext(line: str) -> bool:
    return line.startswith("[ext_resource") and 'type="PackedScene"' in line


def analyze_graph(merged: dict[str, str]) -> tuple[bool, list[list[str]]]:
    root_uids: dict[str, str] = {}
    edges: list[tuple[str, str]] = []
    for rel, text in merged.items():
        for line in text.splitlines():
            if line.startswith("[gd_scene") and 'uid="' in line:
                m = UID_RE.search(line)
                if m:
                    root_uids[rel] = m.group(1)
                break
    for rel, text in merged.items():
        src = root_uids.get(rel)
        if not src:
            continue
        for line in text.splitlines():
            if not _is_packed_scene_ext(line):
                continue
            m = UID_RE.search(line)
            if m:
                edges.append((src, m.group(1)))
    graph: dict[str, set[str]] = {}
    for a, b in edges:
        graph.setdefault(a, set()).add(b)
    cycles: list[list[str]] = []
    visited: set[str] = set()
    stack: set[str] = set()
    path: list[str] = []

    def dfs(node: str) -> None:
        if node in stack:
            idx = path.index(node)
            cycles.append(path[idx:] + [node])
            return
        if node in visited:
            return
        visited.add(node)
        stack.add(node)
        path.append(node)
        for nxt in graph.get(node, ()):
            dfs(nxt)
        path.pop()
        stack.remove(node)

    for node in graph:
        dfs(node)
    return len(cycles) == 0, cycles


def find_orphans(merged: dict[str, str]) -> list[dict[str, str]]:
    present: set[str] = set()
    refs: list[tuple[str, str]] = []
    for rel, text in merged.items():
        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            if i == 1 and line.startswith("[gd_scene"):
                m = UID_RE.search(line)
                if m:
                    present.add(m.group(1))
            for m in UID_RE.finditer(line):
                if i == 1 and line.startswith("[gd_scene"):
                    continue
                refs.append((rel, m.group(1)))
    orphans: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for rel, uid in refs:
        key = (rel, uid)
        if key in seen:
            continue
        seen.add(key)
        if uid not in present:
            orphans.append({"file": rel, "uid": uid})
    return orphans


def canonicalize(value):
    if isinstance(value, Mapping):
        return {k: canonicalize(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        return [canonicalize(v) for v in value]
    return value


def build_ledger(merged: dict[str, str]) -> dict:
    entries = []
    for path in sorted(merged.keys()):
        normalized = normalize_lf(merged[path])
        entries.append(
            {
                "path": path,
                "content_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
            }
        )
    body = {"entries": entries}
    checksum = hashlib.sha256(
        json.dumps(canonicalize(body), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    body["checksum"] = checksum
    return body


def effective_base(scenario: dict, seed: int, seeds_cfg: dict) -> str:
    if seed % seeds_cfg["base_flip_seed_mod"] == 1:
        return scenario["branches"]["left"]
    return scenario["branches"]["base"]


def reference_apply(
    tree: Path,
    base: str,
    left: str,
    right: str,
    seed: int,
    fixtures_root: Path | None = None,
) -> dict:
    fixtures_root = fixtures_root or tree.parent.parent
    tree_meta = json.loads((tree / "tree.json").read_text(encoding="utf-8"))
    remap = build_remap(tree, seed, fixtures_root)
    merged: dict[str, str] = {}
    for rel in tree_meta.get("files", []):
        if rel in tree_meta.get("delete_on_merge", []):
            continue
        base_t = apply_remap(read_branch(tree, base, rel), remap)
        left_t = apply_remap(read_branch(tree, left, rel), remap)
        right_t = apply_remap(read_branch(tree, right, rel), remap)
        out = merge_three_way(base_t, left_t, right_t, base)
        merged[rel] = normalize_lf(out)
    uid_graph_ok, cycles = analyze_graph(merged)
    orphans = find_orphans(merged)
    ledger = build_ledger(merged)
    return {
        "tree": str(tree),
        "base": base,
        "left": left,
        "right": right,
        "seed": seed,
        "merged_files": merged,
        "uid_graph_ok": uid_graph_ok,
        "cycles": cycles,
        "orphans": orphans,
        "ledger": ledger,
    }
