"""Independent PEP 440 wheel resolution contract math."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def parse_py_version(v: str) -> tuple[int, int]:
    parts = v.strip().split(".")
    major = int(parts[0]) if parts else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    return major, minor


def split_epoch(v: str) -> tuple[int, str]:
    if ":" in v:
        e, rest = v.split(":", 1)
        return int(e), rest
    return 0, v


def release_key(v: str) -> list[Any]:
    v = v.split("+")[0]
    v = re.sub(r"\.post\d+", "", v)
    v = re.sub(r"\.dev\d+", "", v)
    local = v
    if "-" in local:
        local = local.split("-", 1)[0]
    parts: list[Any] = []
    for seg in local.split("."):
        if "~" in seg:
            base, _ = seg.split("~", 1)
            parts.append((0, base))
        else:
            parts.append((1, seg))
    return parts


def pep440_gt(a: str, b: str) -> bool:
    ea, ra = split_epoch(a)
    eb, rb = split_epoch(b)
    if ea != eb:
        return ea > eb
    ka, kb = release_key(ra), release_key(rb)
    if ka != kb:
        return ka > kb
    return ra > b  # post/local tie-break simplified


def marker_ok(expr: str, python: str, platform: str, arch: str) -> bool:
    expr = expr.strip()
    if not expr:
        return True
    if expr.startswith("python_version>="):
        need = expr.split(">=", 1)[1].strip().strip('"').strip("'")
        return parse_py_version(python) >= parse_py_version(need)
    if expr.startswith("sys_platform=="):
        need = expr.split("==", 1)[1].strip().strip('"').strip("'")
        return platform == need
    if expr.startswith("platform_machine=="):
        need = expr.split("==", 1)[1].strip().strip('"').strip("'")
        return arch == need
    return True


def tag_compatible(tag: str, python: str, platform: str, arch: str) -> bool:
    parts = tag.split("-")
    if len(parts) < 3:
        return False
    py_tag, abi, plat = parts[0], parts[1], parts[-1]
    py_num = python.replace(".", "")
    if abi == "abi3":
        py_ok = py_tag.startswith("cp") and int(py_tag[2:]) <= int(f"3{py_num[1:]}" if py_num.startswith("3") else py_num)
    else:
        py_ok = py_tag == f"cp{py_num}"
    plat_ok = plat in (f"{platform}_{arch}", "any")
    return py_ok and plat_ok


def matches_spec(version: str, spec: str) -> bool:
    spec = spec.strip()
    if spec.startswith(">="):
        bound = spec[2:].strip()
        return pep440_gt(version, bound) or version == bound
    if spec.startswith("<="):
        bound = spec[2:].strip()
        return pep440_gt(bound, version) or version == bound
    if spec.startswith("!="):
        return version != spec[2:].strip()
    if spec.startswith("=="):
        return version == spec[2:].strip()
    return True


def load_packages(scenario_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    idx = scenario_dir / "indices"
    for path in sorted(idx.glob("*.json")):
        sid = path.stem
        for row in json.loads(path.read_text(encoding="utf-8")):
            rows.append({**row, "source_id": sid})
    return rows


def snapshot_digest(
    run_id: str,
    fp: str,
    python: str,
    platform: str,
    arch: str,
    packages: list[dict[str, Any]],
) -> str:
    body = {
        "index_fingerprint": fp,
        "packages": [{"package": p["package"], "version": p["version"]} for p in packages],
        "run_id": run_id,
        "target_arch": arch,
        "target_platform": platform,
        "target_python": python,
    }
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def select_candidate(
    packages: list[dict[str, Any]],
    pkg: str,
    spec: str,
    python: str,
    platform: str,
    arch: str,
) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    for row in packages:
        if row["package"] != pkg or row.get("yanked"):
            continue
        rp = row.get("requires_python")
        if rp and not marker_ok(rp, python, platform, arch):
            continue
        if not matches_spec(row["version"], spec):
            continue
        tags = [w["tag"] for w in row.get("wheels", [])]
        tag = next((t for t in sorted(tags) if tag_compatible(t, python, platform, arch)), None)
        if tag is None:
            continue
        if best is None or pep440_gt(row["version"], best["version"]):
            best = {**row, "wheel_tag": tag}
    if best is None:
        return {
            "package": pkg,
            "selected_version": None,
            "wheel_tag": None,
            "source_id": None,
            "reason": "no_candidate",
        }
    return {
        "package": pkg,
        "selected_version": best["version"],
        "wheel_tag": best["wheel_tag"],
        "source_id": best.get("source_id"),
        "reason": "wheel_match",
    }


def reference_report(scenario_dir: Path, run_id: str) -> dict[str, Any]:
    meta = json.loads((scenario_dir / "scenario.json").read_text(encoding="utf-8"))
    packages = load_packages(scenario_dir)
    python = meta.get("target_python", "3.10")
    platform = meta.get("target_platform", "linux")
    arch = meta.get("target_arch", "x86_64")
    _index_names = sorted(p.name for p in (scenario_dir / "indices").glob("*.json"))
    _ = hashlib.sha256(json.dumps(_index_names).encode()).hexdigest()
    candidates = [
        select_candidate(packages, q["package"], q["spec"], python, platform, arch)
        for q in meta.get("queries", [])
    ]
    candidates.sort(key=lambda c: c["package"])
    # Compact JSON matching serde_json::to_string field order in candidate-emit-contract.md
    audit = hashlib.sha256(
        json.dumps(candidates, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "run_id": run_id,
        "candidates": candidates,
        "summary": {"query_count": len(candidates)},
        "audit_digest": audit,
    }
