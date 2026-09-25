"""Independent reference renderer for dosbox-plan fixtures."""

from __future__ import annotations

import json
import re
from pathlib import Path

CATALOG: dict[str, str] = {
    "001-basic-mount": "default",
    "002-config-precedence": "default",
    "003-imgmount-remap": "default",
    "004-duplicate-stack": "default",
    "005-line-continuation": "default",
    "006-invalid-drive": "default",
    "007-multi-file": "default",
    "008-interleaved-sections": "default",
}


def load_config(path: Path | None = None) -> dict:
    cfg_path = path or Path("/app/config/plan.json")
    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    return {
        "fail_on_invalid_drive": bool(data.get("fail_on_invalid_drive", True)),
        "default_profile": str(data.get("default_profile", "default")),
    }


def read_manifest(conf_dir: Path) -> list[str]:
    manifest = conf_dir / "manifest.txt"
    if not manifest.is_file():
        raise FileNotFoundError(f"missing manifest: {manifest}")
    files: list[str] = []
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        conf_path = conf_dir / line
        if not conf_path.is_file():
            raise FileNotFoundError(f"missing conf file: {conf_path}")
        files.append(line)
    if not files:
        raise ValueError("empty manifest")
    return files


def join_continuations(text: str) -> list[str]:
    physical = text.splitlines()
    out: list[str] = []
    carry = ""
    idx = 0
    while idx < len(physical):
        line = physical[idx].rstrip()
        if re.search(r"\\[ \t]*$", line):
            carry += line[: line.rfind("\\")].rstrip()
            idx += 1
            continue
        if carry:
            cont = physical[idx].lstrip()
            line = carry + cont
            carry = ""
        out.append(line)
        idx += 1
    if carry:
        out.append(carry)
    return out


def parse_sections(text: str, source_file: str) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    current: str | None = None
    for raw in join_continuations(text):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].lower()
            continue
        if current is None:
            continue
        rows.append((current, source_file, line))
    return rows


def parse_remap(cmd: str) -> tuple[str, str] | None:
    parts = cmd.split()
    if not parts or parts[0].lower() != "remap_drive":
        return None
    if len(parts) < 3:
        return None
    frm = parts[1].rstrip(":").upper()
    to = parts[2].rstrip(":").upper()
    return frm, to


def parse_mount(cmd: str) -> tuple[str, str, str] | None:
    parts = cmd.split()
    if len(parts) < 3:
        return None
    op = parts[0].lower()
    if op not in ("mount", "imgmount"):
        return None
    drive = parts[1].rstrip(":").upper()
    path = parts[2]
    return op, drive, path


def valid_drive(drive: str) -> bool:
    return len(drive) == 1 and "A" <= drive <= "Z"


def apply_path_remap(path: str, remaps: dict[str, str]) -> str:
    if len(path) >= 2 and path[1] == ":":
        letter = path[0].upper()
        if letter in remaps:
            return remaps[letter] + path[1:]
    return path


def collect_rows(conf_dir: Path, files: list[str]) -> list[tuple[str, str, str]]:
    per_file: list[tuple[str, str, str]] = []
    for name in files:
        text = (conf_dir / name).read_text(encoding="utf-8")
        per_file.extend(parse_sections(text, name))
    config_rows = [r for r in per_file if r[0] == "config"]
    autoexec_rows = [r for r in per_file if r[0] == "autoexec"]
    return config_rows + autoexec_rows


def build_plan(
    conf_dir: Path,
    profile: str = "default",
    config: dict | None = None,
) -> tuple[dict, int]:
    cfg = config or load_config()
    errors: list[str] = []
    warnings: list[str] = []
    remaps_list: list[dict[str, str]] = []
    remaps: dict[str, str] = {}
    lineage: list[dict] = []

    if not conf_dir.is_dir():
        errors.append(f"missing conf dir: {conf_dir}")
        doc = _empty_doc(conf_dir, profile, lineage, remaps_list, warnings, errors)
        return doc, 1

    try:
        files = read_manifest(conf_dir)
    except (FileNotFoundError, ValueError) as exc:
        errors.append(str(exc))
        doc = _empty_doc(conf_dir, profile, lineage, remaps_list, warnings, errors)
        return doc, 1

    rows = collect_rows(conf_dir, files)

    for _sec, _src, cmd in rows:
        if _sec != "config":
            continue
        parsed = parse_remap(cmd)
        if parsed is None:
            continue
        frm, to = parsed
        remaps[frm] = to
        remaps_list.append({"from": frm, "to": to})

    seq = 0
    stack_counter: dict[str, int] = {}
    for _sec, src, cmd in rows:
        if _sec != "autoexec":
            continue
        parsed = parse_mount(cmd)
        if parsed is None:
            continue
        op, drive, path = parsed
        if not valid_drive(drive):
            errors.append(f"invalid drive letter: {drive}")
            if cfg["fail_on_invalid_drive"]:
                doc = _empty_doc(
                    conf_dir, profile, lineage, remaps_list, warnings, errors
                )
                doc["lineage"] = lineage
                doc["stats"] = _stats(lineage)
                return doc, 2
            continue
        effective_drive = remaps.get(drive, drive)
        effective_path = apply_path_remap(path, remaps)
        seq += 1
        lineage.append(
            {
                "seq": seq,
                "op": op,
                "drive": effective_drive,
                "path": effective_path,
                "source_section": "autoexec",
                "source_file": src,
            }
        )
        stack_counter[effective_drive] = stack_counter.get(effective_drive, 0) + 1

    doc = {
        "plan_version": 1,
        "profile": profile,
        "conf_dir": str(conf_dir),
        "lineage": lineage,
        "remaps": remaps_list,
        "stats": _stats(lineage, stack_counter),
        "warnings": warnings,
        "errors": errors,
    }
    return doc, 0


def _stats(lineage: list[dict], stack_counter: dict[str, int] | None = None) -> dict:
    if stack_counter is None:
        stack_counter = {}
        for entry in lineage:
            d = entry["drive"]
            stack_counter[d] = stack_counter.get(d, 0) + 1
    stack_depth = max(stack_counter.values()) if stack_counter else 0
    return {
        "mount_count": sum(1 for e in lineage if e["op"] == "mount"),
        "imgmount_count": sum(1 for e in lineage if e["op"] == "imgmount"),
        "stack_depth": stack_depth,
    }


def _empty_doc(
    conf_dir: Path,
    profile: str,
    lineage: list,
    remaps: list,
    warnings: list,
    errors: list,
) -> dict:
    return {
        "plan_version": 1,
        "profile": profile,
        "conf_dir": str(conf_dir),
        "lineage": lineage,
        "remaps": remaps,
        "stats": _stats(lineage),
        "warnings": warnings,
        "errors": errors,
    }


def build_seed_conf_text(seed: str) -> str:
    """Build seeded conf with swapped section order and imgmount edge case."""
    digest = sum(ord(c) for c in seed) % 2
    if digest == 0:
        return (
            "[autoexec]\n"
            "imgmount D D:/seed/disc.iso -t iso\n"
            "[config]\n"
            "remap_drive D E\n"
        )
    return (
        "[config]\n"
        "remap_drive C D\n"
        "[autoexec]\n"
        "mount C /seed/games\n"
        "imgmount D D:/seed/alt.iso -t iso\n"
        "[config]\n"
        "remap_drive D F\n"
    )


def build_seed_manifest() -> str:
    return "seed.conf\n"
