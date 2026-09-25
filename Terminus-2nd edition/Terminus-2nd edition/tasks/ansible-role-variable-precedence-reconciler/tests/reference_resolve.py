"""Independent reference for ansible-var-merge resolve."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import yaml

APP = Path("/app")
CLI = APP / "bin/ansible-var-merge"


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {} if data is None else dict(data)


def inventory_groups(host: str, inventory_root: Path) -> list[str]:
    groups: list[str] = []
    current: str | None = None
    for raw in (inventory_root / "hosts.ini").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            header = line[1:-1]
            if ":children" in header or ":vars" in header:
                current = None
                continue
            current = header
            continue
        if current and line.split()[0] == host:
            groups.append(current)
    return sorted(groups)


def deep_merge(base: dict, overlay: dict) -> dict:
    out = dict(base)
    for key, value in overlay.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def apply_layer(base: dict, overlay: dict, behaviour: str) -> dict:
    if behaviour == "merge":
        return deep_merge(base, overlay)
    merged = dict(base)
    merged.update(overlay)
    return merged


def resolve_inventory(host: str, inventory_root: Path, behaviour: str) -> dict:
    merged: dict = {}
    group_files = [inventory_root / "group_vars" / "all.yml"]
    for group in inventory_groups(host, inventory_root):
        path = inventory_root / "group_vars" / f"{group}.yml"
        if path.exists():
            group_files.append(path)
    for path in group_files:
        if path.exists():
            merged = apply_layer(merged, load_yaml(path), behaviour)
    host_path = inventory_root / "host_vars" / f"{host}.yml"
    if host_path.exists():
        merged = apply_layer(merged, load_yaml(host_path), behaviour)
    return merged


def resolve_role_defaults(role_names: list[str], roles_root: Path, behaviour: str) -> dict:
    merged: dict = {}
    for role in role_names:
        defaults = roles_root / role / "defaults" / "main.yml"
        if defaults.exists():
            merged = apply_layer(merged, load_yaml(defaults), behaviour)
    return merged


def resolve_role_vars_only(role_names: list[str], roles_root: Path, behaviour: str) -> dict:
    merged: dict = {}
    for role in role_names:
        role_vars = roles_root / role / "vars" / "main.yml"
        if role_vars.exists():
            merged = apply_layer(merged, load_yaml(role_vars), behaviour)
    return merged


def resolve_roles(role_names: list[str], roles_root: Path, behaviour: str) -> dict:
    merged = resolve_role_defaults(role_names, roles_root, behaviour)
    return apply_layer(merged, resolve_role_vars_only(role_names, roles_root, behaviour), behaviour)


def resolve_includes(playbook: Path, manifest: dict, behaviour: str) -> dict:
    merged: dict = {}
    playbook_dir = playbook.parent
    includes = sorted(manifest.get("include_vars", []), key=lambda item: int(item["depth"]))
    for entry in includes:
        path = (playbook_dir / entry["path"]).resolve()
        merged = apply_layer(merged, load_yaml(path), behaviour)
    return merged


def reference_resolve(
    playbook: Path,
    inventory_root: Path,
    host: str,
    seed: str,
    extra_vars: Path | None = None,
) -> dict:
    manifest = load_yaml(playbook)
    behaviour = manifest.get("hash_behaviour", "replace")
    merged: dict = {}
    roles = manifest.get("roles", [])
    if roles:
        merged = apply_layer(
            merged,
            resolve_role_defaults(roles, APP / "roles", behaviour),
            behaviour,
        )
    merged = apply_layer(merged, resolve_inventory(host, inventory_root, behaviour), behaviour)
    if roles:
        merged = apply_layer(
            merged,
            resolve_role_vars_only(roles, APP / "roles", behaviour),
            behaviour,
        )
    merged = apply_layer(merged, resolve_includes(playbook, manifest, behaviour), behaviour)
    merged = apply_layer(merged, manifest.get("vars", {}), behaviour)
    if extra_vars and extra_vars.exists():
        merged = apply_layer(merged, load_yaml(extra_vars), behaviour)
    return {"host": host, "seed": seed, "merged": merged}


def run_cli_resolve(
    playbook: Path,
    inventory_root: Path,
    host: str,
    seed: str,
    out: Path,
    extra_vars: Path | None = None,
) -> int:
    cmd = [
        str(CLI),
        "resolve",
        "--playbook",
        str(playbook),
        "--inventory",
        str(inventory_root),
        "--host",
        host,
        "--seed",
        seed,
        "--out",
        str(out),
    ]
    if extra_vars is not None:
        cmd.extend(["--extra-vars", str(extra_vars)])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode


def load_cli_export(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def seeded_var_name(seed: str, prefix: str = "probe") -> str:
    digest = hashlib.sha256(seed.encode()).hexdigest()[:8]
    return f"{prefix}_{digest}"


def seeded_var_value(seed: str) -> int:
    return int(hashlib.sha256(f"value:{seed}".encode()).hexdigest()[:6], 16) % 9000 + 1000


def copy_inventory_with_host_var(
    tmp_root: Path,
    seed: str,
    host: str = "web01",
) -> Path:
    inv = tmp_root / "inventory"
    shutil.copytree(APP / "inventory", inv)
    key = seeded_var_name(seed)
    value = seeded_var_value(seed)
    host_file = inv / "host_vars" / f"{host}.yml"
    doc = load_yaml(host_file)
    doc[key] = value
    host_file.write_text(yaml.safe_dump(doc, sort_keys=True), encoding="utf-8")
    return inv
