"""Independent reference resolver for Lutris registry fixtures."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG = {
    "prefix_root": "/app",
    "fail_on_missing_slug": True,
    "fail_on_dxvk_mismatch": True,
}

CATALOG: dict[str, str] = {
    "001-transitive-runner": "frontier-rpg",
    "002-symlink-prefix": "symlink-game",
    "003-dxvk-semver": "semver-game",
    "004-duplicate-merge": "dup-game",
    "005-missing-runner": "orphan-game",
    "006-deep-chain": "deep-root",
    "007-requires-cycle": "cycle-root",
    "008-missing-slug": "ghost-game",
    "009-conflicting-duplicate": "clash-game",
}


@dataclass
class Entry:
    slug: str
    runner: str | None = None
    prefix: str | None = None
    dxvk_pin: str | None = None
    requires: list[str] = field(default_factory=list)
    provides: dict[str, str] = field(default_factory=dict)


def load_config(path: Path | None = None) -> dict:
    cfg_path = path or Path("/app/config/resolve.json")
    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    return {
        "prefix_root": str(data.get("prefix_root", "/app")),
        "fail_on_missing_slug": bool(data.get("fail_on_missing_slug", True)),
        "fail_on_dxvk_mismatch": bool(data.get("fail_on_dxvk_mismatch", True)),
    }


def parse_registry(path: Path) -> list[Entry]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    entries: list[Entry] = []
    current: Entry | None = None
    section: str | None = None

    def flush() -> None:
        nonlocal current
        if current is not None:
            entries.append(current)
            current = None

    for raw in lines:
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if re.match(r"^entries:\s*$", line):
            continue
        m_item = re.match(r"^\s*-\s+slug:\s*(.+)$", line)
        if m_item:
            flush()
            slug = m_item.group(1).strip().strip('"').strip("'")
            current = Entry(slug=slug)
            section = None
            continue
        if current is None:
            continue
        m_runner = re.match(r"^\s+runner:\s*(.+)$", line)
        if m_runner:
            val = m_runner.group(1).strip()
            current.runner = None if val in ("null", "~", "") else val.strip('"').strip("'")
            continue
        m_prefix = re.match(r"^\s+prefix:\s*(.+)$", line)
        if m_prefix:
            current.prefix = m_prefix.group(1).strip().strip('"').strip("'")
            continue
        m_pin = re.match(r"^\s+dxvk_pin:\s*(.+)$", line)
        if m_pin:
            current.dxvk_pin = m_pin.group(1).strip().strip('"').strip("'")
            continue
        if re.match(r"^\s+requires:\s*$", line):
            section = "requires"
            continue
        if re.match(r"^\s+provides:\s*$", line):
            section = "provides"
            continue
        m_req = re.match(r"^\s+-\s+(.+)$", line)
        if m_req and section == "requires":
            current.requires.append(m_req.group(1).strip().strip('"').strip("'"))
            continue
        m_provide = re.match(r"^\s+([a-zA-Z0-9_]+):\s*(.+)$", line)
        if m_provide and section == "provides":
            key = m_provide.group(1)
            val = m_provide.group(2).strip().strip('"').strip("'")
            current.provides[key] = val
            continue

    flush()
    return entries


def merge_entries(entries: list[Entry]) -> tuple[dict[str, Entry], list[str], list[str]]:
    merged: dict[str, Entry] = {}
    warnings: list[str] = []
    errors: list[str] = []

    for entry in entries:
        if entry.slug not in merged:
            merged[entry.slug] = Entry(
                slug=entry.slug,
                runner=entry.runner,
                prefix=entry.prefix,
                dxvk_pin=entry.dxvk_pin,
                requires=list(entry.requires),
                provides=dict(entry.provides),
            )
            continue
        warnings.append(f"duplicate slug {entry.slug} merged")
        base = merged[entry.slug]
        if base.runner and entry.runner and base.runner != entry.runner:
            errors.append(f"conflicting runner for slug {entry.slug}")
        for dep in entry.requires:
            if dep not in base.requires:
                base.requires.append(dep)
        for key, val in entry.provides.items():
            if key in base.provides and base.provides[key] != val:
                errors.append(f"conflicting provides {key} for slug {entry.slug}")
            base.provides[key] = val

    for entry in merged.values():
        entry.requires = sorted(set(entry.requires))
    return merged, warnings, errors


def _semver_ok(version: str, pin: str) -> bool:
    def parse(v: str) -> tuple[int, int, int]:
        parts = v.strip().split(".")
        nums = [int(parts[i]) if i < len(parts) else 0 for i in range(3)]
        return tuple(nums)

    pin = pin.strip()
    if pin.startswith(">="):
        return parse(version) >= parse(pin[2:])
    return version == pin


def _canonical_prefix(prefix_root: str, relative: str | None) -> str | None:
    if not relative:
        return None
    joined = os.path.join(prefix_root, relative)
    return os.path.realpath(joined)


def build_resolve(registry_dir: Path, root_slug: str, cfg: dict | None = None) -> tuple[dict, int]:
    cfg = cfg or load_config()
    entries = parse_registry(registry_dir / "registry.yml")
    merged, warnings, errors = merge_entries(entries)

    if errors:
        doc = _empty_doc(registry_dir, root_slug, warnings, errors)
        return doc, 2

    if root_slug not in merged:
        errors.append(f"missing slug {root_slug}")
        doc = _empty_doc(registry_dir, root_slug, warnings, errors)
        return doc, 1 if cfg["fail_on_missing_slug"] else 0

    requires: dict[str, list[str]] = {slug: list(e.requires) for slug, e in merged.items()}
    exists = set(merged.keys())

    def check_missing(slug: str, seen: set[str]) -> None:
        if slug in seen:
            return
        seen.add(slug)
        for dep in requires.get(slug, []):
            if dep not in exists:
                errors.append(f"missing slug {dep}")
            else:
                check_missing(dep, seen)

    check_missing(root_slug, set())

    cycles: list[str] = []
    if not errors:
        visiting: set[str] = set()
        stack: set[str] = set()

        def dfs(slug: str) -> None:
            visiting.add(slug)
            stack.add(slug)
            for dep in requires.get(slug, []):
                if dep in stack:
                    cycles.append(f"{dep},{slug}")
                    continue
                if dep not in visiting:
                    dfs(dep)
            stack.remove(slug)

        dfs(root_slug)

    order: list[str] = []
    if not errors and not cycles:
        visited: set[str] = set()

        def topo(slug: str) -> None:
            for dep in sorted(requires.get(slug, [])):
                topo(dep)
            if slug not in visited:
                order.append(slug)
                visited.add(slug)

        topo(root_slug)

    runner: str | None = None
    for slug in order:
        r = merged[slug].runner
        if r:
            runner = r

    if not errors and not cycles and not runner:
        errors.append(f"missing runner for {root_slug}")

    dxvk_version: str | None = None
    for slug in order:
        if "dxvk_version" in merged[slug].provides:
            dxvk_version = merged[slug].provides["dxvk_version"]
            break

    root = merged[root_slug]
    if root.dxvk_pin:
        if not dxvk_version:
            errors.append(f"dxvk pin {root.dxvk_pin} not satisfied by ")
        elif not _semver_ok(dxvk_version, root.dxvk_pin):
            errors.append(f"dxvk pin {root.dxvk_pin} not satisfied by {dxvk_version}")

    max_depth = 0
    if not cycles:

        def depth(slug: str, d: int) -> None:
            nonlocal max_depth
            if d > max_depth:
                max_depth = d
            for dep in requires.get(slug, []):
                depth(dep, d + 1)

        depth(root_slug, 0)

    closure_set = set(order)
    edge_count = sum(
        1
        for slug in order
        for dep in requires.get(slug, [])
        if dep in closure_set
    )

    exit_code = 0
    if cycles:
        exit_code = 2
    elif errors:
        if any("conflicting" in e for e in errors):
            exit_code = 2
        elif cycles:
            exit_code = 2
        else:
            exit_code = 1

    doc = {
        "resolve_version": 1,
        "registry_dir": str(registry_dir),
        "root_slug": root_slug,
        "runner": runner,
        "prefix": _canonical_prefix(cfg["prefix_root"], root.prefix),
        "dxvk_version": dxvk_version,
        "closure": [] if cycles else order,
        "warnings": warnings,
        "errors": errors,
        "cycles": cycles,
        "stats": {
            "entry_count": len(merged),
            "edge_count": edge_count,
            "max_depth": max_depth,
        },
    }
    return doc, exit_code


def _empty_doc(registry_dir: Path, root_slug: str, warnings: list[str], errors: list[str]) -> dict:
    return {
        "resolve_version": 1,
        "registry_dir": str(registry_dir),
        "root_slug": root_slug,
        "runner": None,
        "prefix": None,
        "dxvk_version": None,
        "closure": [],
        "warnings": warnings,
        "errors": errors,
        "cycles": [],
        "stats": {"entry_count": 0, "edge_count": 0, "max_depth": 0},
    }


def hashlib_hex(seed: str, offset: int) -> str:
    import hashlib

    return hashlib.sha256(f"{seed}:{offset}".encode()).hexdigest()


def build_seed_registry_text(seed: str) -> str:
    pin_minor = int(hashlib_hex(seed, 0)[:2], 16) % 5 + 10
    pin_patch = int(hashlib_hex(seed, 1)[:2], 16) % 9
    ver_minor = pin_minor - 1
    ver_patch = (pin_patch + 3) % 10
    wine_tag = hashlib_hex(seed, 2)[:4]
    return f"""entries:
  - slug: seed-game
    runner: null
    requires:
      - seed-dxvk
    prefix: prefixes/active/stellaris
    dxvk_pin: ">=2.{pin_minor}.{pin_patch}"
  - slug: seed-dxvk
    runner: null
    requires:
      - seed-wine
    provides:
      dxvk_version: "2.{ver_minor}.{ver_patch}"
  - slug: seed-wine
    runner: seed-wine-{wine_tag}
    requires: []
"""
