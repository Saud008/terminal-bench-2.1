"""Independent reference implementation for the workshop-plan pipeline.

This module mirrors the locked plan contract:

* VDF manifests are parsed into declaration-ordered TSV rows.
* Dependency admission uses numeric semver comparison.
* Mount order is produced with Kahn's algorithm, dependency-first, sorting
  each ready batch in ASCII-ascending order.
* Cycles are reported by walking from the lexicographically smallest node in
  the cycle, following the lex-first outgoing neighbour in the
  dependency->dependent adjacency, including the return to the start.

The verifier tests compare the CLI output against ``build_plan`` output.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

RUN_SEQ_PATH = Path("/app/state/run-seq.json")


# --------------------------------------------------------------------------
# VDF parsing
# --------------------------------------------------------------------------
def _tokenize(text: str):
    toks = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif c == "{":
            toks.append(("open", "{"))
            i += 1
        elif c == "}":
            toks.append(("close", "}"))
            i += 1
        elif c == '"':
            i += 1
            buf = []
            while i < n and text[i] != '"':
                if text[i] == "\\" and i + 1 < n:
                    buf.append(text[i + 1])
                    i += 2
                else:
                    buf.append(text[i])
                    i += 1
            i += 1
            toks.append(("str", "".join(buf)))
        else:
            start = i
            while i < n and text[i] not in ' \t\r\n{}"':
                i += 1
            toks.append(("str", text[start:i]))
    return toks


def _parse_block(toks, i):
    items = []
    while i < len(toks):
        t, v = toks[i]
        if t == "close":
            return items, i + 1
        key = v
        i += 1
        if i >= len(toks):
            break
        nt, nv = toks[i]
        if nt == "open":
            block, i = _parse_block(toks, i + 1)
            items.append((key, block))
        else:
            items.append((key, nv))
            i += 1
    return items, i


def _find_block(items, name):
    for k, v in items:
        if k == name and isinstance(v, list):
            return v
    return None


def _emit_lines(text: str):
    toks = _tokenize(text)
    root, _ = _parse_block(toks, 0)
    coll = None
    for _k, v in root:
        if isinstance(v, list):
            coll = v
            break
    lines: list[str] = []
    if coll is None:
        return lines
    mods = _find_block(coll, "mods")
    if mods is None:
        return lines
    for mod_id, mod_body in mods:
        if not isinstance(mod_body, list):
            continue
        version = ""
        depends = None
        for k, v in mod_body:
            if k == "version" and isinstance(v, str):
                version = v
            elif k == "depends" and isinstance(v, list):
                depends = v
        lines.append(f"MOD\t{mod_id}\t{version}")
        if depends:
            for dep_id, dep_body in depends:
                if not isinstance(dep_body, list):
                    continue
                constraint = ""
                optional = "0"
                for k, v in dep_body:
                    if k == "version" and isinstance(v, str):
                        constraint = v
                    elif k == "optional" and isinstance(v, str):
                        optional = v
                lines.append(f"DEP\t{mod_id}\t{dep_id}\t{constraint}\t{optional}")
    return lines


def parsed_lines_for_manifest(manifest_dir: Path) -> list[str]:
    """Return the declaration-ordered TSV rows for ``manifest_dir``."""
    manifest_file = Path(manifest_dir) / "manifest.vdf"
    text = manifest_file.read_text(encoding="utf-8", errors="replace")
    return _emit_lines(text)


# --------------------------------------------------------------------------
# Staging metadata
# --------------------------------------------------------------------------
def _staged_bytes(lines: list[str]) -> bytes:
    if not lines:
        return b""
    return ("\n".join(lines) + "\n").encode("utf-8")


def reference_staging_meta(lines: list[str]) -> dict:
    """Return the expected ``staging-meta.json`` document for ``lines``."""
    blob = _staged_bytes(lines)
    return {
        "staging_version": 1,
        "parsed_sha256": hashlib.sha256(blob).hexdigest(),
        "line_count": len(lines),
    }


# --------------------------------------------------------------------------
# Config + fingerprint
# --------------------------------------------------------------------------
def load_config(config_path: Path) -> dict:
    return json.loads(Path(config_path).read_text(encoding="utf-8"))


def input_fingerprint(manifest_dir: Path, cfg: dict) -> str:
    manifest_file = Path(manifest_dir) / "manifest.vdf"
    cfg_blob = json.dumps(cfg, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(manifest_file.read_bytes() + b"\n" + cfg_blob).hexdigest()


# --------------------------------------------------------------------------
# Semver
# --------------------------------------------------------------------------
def _parse_constraint(c: str):
    for op in (">=", "<=", "==", ">", "<"):
        if c.startswith(op):
            return op, c[len(op):].strip()
    return ">=", c.strip()


def _ver_key(v: str):
    key = []
    for part in v.split("."):
        num = ""
        for ch in part:
            if ch.isdigit():
                num += ch
            else:
                break
        key.append(int(num) if num else 0)
    return key


def _semver_ok(have: str, constraint: str) -> bool:
    op, want = _parse_constraint(constraint)
    a = _ver_key(have)
    b = _ver_key(want)
    n = max(len(a), len(b))
    a += [0] * (n - len(a))
    b += [0] * (n - len(b))
    if op == ">=":
        return a >= b
    if op == ">":
        return a > b
    if op == "<=":
        return a <= b
    if op == "<":
        return a < b
    if op == "==":
        return a == b
    return a >= b


# --------------------------------------------------------------------------
# Dependency graph + topo
# --------------------------------------------------------------------------
def _build_graph(lines: list[str], include_optional: bool):
    mods: dict[str, str] = {}
    mod_order: list[str] = []
    deps: list[tuple[str, str, str, str]] = []
    for line in lines:
        parts = line.split("\t")
        if parts[0] == "MOD":
            mid = parts[1] if len(parts) > 1 else ""
            ver = parts[2] if len(parts) > 2 else ""
            if mid not in mods:
                mod_order.append(mid)
            mods[mid] = ver
        elif parts[0] == "DEP":
            frm = parts[1] if len(parts) > 1 else ""
            to = parts[2] if len(parts) > 2 else ""
            constraint = parts[3] if len(parts) > 3 else ""
            optional = parts[4] if len(parts) > 4 else "0"
            deps.append((frm, to, constraint, optional))

    edges: list[tuple[str, str, str]] = []
    errors: list[str] = []
    edge_count = 0
    for frm, to, constraint, optional in deps:
        is_opt = optional == "1"
        if is_opt and not include_optional:
            continue
        if to not in mods:
            if is_opt:
                continue
            errors.append(f"missing required dependency: {frm} -> {to} ({constraint})")
            continue
        have = mods[to]
        if not _semver_ok(have, constraint):
            errors.append(
                f"semver constraint failed: {frm} requires {to} {constraint} (have {have})"
            )
            continue
        edges.append((to, frm, "1" if is_opt else "0"))
        edge_count += 1

    return mod_order, edges, errors, edge_count


def _topo(mod_order: list[str], edges: list[tuple[str, str, str]]):
    nodes = list(mod_order)
    adj: dict[str, list[str]] = {n: [] for n in nodes}
    indeg: dict[str, int] = {n: 0 for n in nodes}
    for a, b, _o in edges:
        adj.setdefault(a, []).append(b)
        indeg[b] = indeg.get(b, 0) + 1

    order: list[str] = []
    processed: set[str] = set()
    indeg2 = dict(indeg)
    ready = sorted([n for n in nodes if indeg2.get(n, 0) == 0])
    while ready:
        for n in ready:
            order.append(n)
            processed.add(n)
        new_ready = []
        for n in ready:
            for m in sorted(adj.get(n, [])):
                indeg2[m] -= 1
                if indeg2[m] == 0 and m not in processed:
                    new_ready.append(m)
        ready = sorted(set(new_ready))

    cycles: list[str] = []
    if len(processed) < len(nodes):
        remaining = sorted([n for n in nodes if n not in processed])
        start = remaining[0]
        path: list[str] = []
        seen: dict[str, int] = {}
        cur = start
        while cur not in seen:
            seen[cur] = len(path)
            path.append(cur)
            nbrs = sorted(adj.get(cur, []))
            if not nbrs:
                break
            cur = nbrs[0]
        if cur in seen:
            idx = seen[cur]
            cyc = path[idx:] + [cur]
            cycles.append("->".join(cyc))

    return order, cycles


# --------------------------------------------------------------------------
# Run sequence
# --------------------------------------------------------------------------
def _run_seq_for(fingerprint: str, exit_code: int) -> int:
    run_seq = 1
    stored_fp = ""
    exists = RUN_SEQ_PATH.is_file()
    if exists:
        data = json.loads(RUN_SEQ_PATH.read_text(encoding="utf-8"))
        run_seq = int(data.get("seq", 1))
        stored_fp = str(data.get("input_fingerprint", ""))
    if exit_code == 0:
        if exists and stored_fp == fingerprint:
            return run_seq
        if exists and stored_fp:
            return run_seq + 1
        return 1
    return run_seq


# --------------------------------------------------------------------------
# Plan
# --------------------------------------------------------------------------
def build_plan(manifest_dir: Path, cfg: dict):
    """Return ``(plan_dict, exit_code)`` for ``manifest_dir`` under ``cfg``."""
    manifest_dir = Path(manifest_dir)
    include_optional = bool(cfg.get("include_optional_edges", True))
    fail_on_missing = bool(cfg.get("fail_on_missing", True))
    emit_on_cycle = bool(cfg.get("emit_on_cycle", False))

    lines = parsed_lines_for_manifest(manifest_dir)
    mod_order, edges, errors, edge_count = _build_graph(lines, include_optional)
    mount_order, cycles = _topo(mod_order, edges)
    mod_count = len(mod_order)

    exit_code = 0
    if errors and fail_on_missing:
        exit_code = 1
    if cycles and not emit_on_cycle:
        mount_order = []
        exit_code = 2

    fingerprint = input_fingerprint(manifest_dir, cfg)
    run_seq = _run_seq_for(fingerprint, exit_code)

    doc = {
        "plan_version": 1,
        "manifest_dir": str(manifest_dir),
        "mount_order": mount_order,
        "errors": errors,
        "cycles": cycles,
        "stats": {
            "mod_count": mod_count,
            "edge_count": edge_count,
        },
        "footer": {"run_seq": run_seq},
    }
    return doc, exit_code


# --------------------------------------------------------------------------
# Seeded anti-hardcoding manifest
# --------------------------------------------------------------------------
def build_seed_manifest(seed: str) -> str:
    """Return a seed-dependent VDF manifest whose mount order starts at seed_hub."""
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8]
    leaf = f"seed_leaf_{digest}"
    return (
        '"WorkshopCollection"\n'
        "{\n"
        '\t"mods"\n'
        "\t{\n"
        '\t\t"seed_hub"\n'
        "\t\t{\n"
        '\t\t\t"version"\t"1.0.0"\n'
        "\t\t}\n"
        f'\t\t"{leaf}"\n'
        "\t\t{\n"
        '\t\t\t"version"\t"1.0.0"\n'
        '\t\t\t"depends"\n'
        "\t\t\t{\n"
        '\t\t\t\t"seed_hub"\n'
        "\t\t\t\t{\n"
        '\t\t\t\t\t"version"\t">=1.0.0"\n'
        '\t\t\t\t\t"optional"\t"0"\n'
        "\t\t\t\t}\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
