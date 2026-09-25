"""Independent reference for hostsatlas staging and exposure reports."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import group_policy
import staging_policy
import vault_policy

SECRET_KEY_RE = re.compile(
    r"^(.*_)?(password|secret|api_key|token|private_key)$", re.IGNORECASE
)
VAULT_PREFIX = vault_policy.VAULT_PREFIX
SEVERITY_WEIGHTS = {
    "vault_exposure": "critical",
    "plaintext_secret": "high",
    "precedence_shadow": "medium",
    "ignored_file_leak": "high",
}

CHILDREN_FIRST = group_policy.CHILDREN_FIRST
HOST_BEFORE_GROUPS = group_policy.HOST_BEFORE_GROUPS
USE_INVENTORY_IGNORE = staging_policy.USE_INVENTORY_IGNORE
DIGEST_FINDINGS = staging_policy.DIGEST_FINDINGS
EXPORT_REOPEN = staging_policy.EXPORT_REOPEN


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def tree_fingerprint(manifest_path: Path, inventory_root: Path) -> str:
    parts: list[bytes] = [manifest_path.read_bytes()]
    for p in sorted(inventory_root.rglob("*")):
        if p.is_file():
            parts.append(str(p.relative_to(inventory_root)).encode())
            parts.append(p.read_bytes())
    return sha256_bytes(b"".join(parts))


def load_simple_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.is_file():
        return data
    current_key: str | None = None
    vault_lines: list[str] = []
    in_vault = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line or line.strip().startswith("#"):
            continue
        if line.strip().startswith("---"):
            continue
        tag_m = re.match(r"^(\w+):\s*!vault\s*$", line.strip())
        if tag_m:
            current_key = tag_m.group(1)
            in_vault = True
            vault_lines = []
            continue
        if in_vault:
            if line.startswith(("  ", "\t")):
                vault_lines.append(line.strip())
                continue
            data[current_key or ""] = "\n".join(vault_lines)
            in_vault = False
            current_key = None
            vault_lines = []
        m = re.match(r"^(\w+):\s*(.+)$", line.strip())
        if m:
            data[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    if in_vault and current_key:
        data[current_key] = "\n".join(vault_lines)
    return data


def is_vault_value(value: str) -> bool:
    return vault_policy.has_vault_prefix(value, VAULT_PREFIX)


def is_secret_key(key: str) -> bool:
    return bool(SECRET_KEY_RE.match(key))


def load_ignore_patterns(inventory_root: Path, ansible_cfg: Path | None) -> list[str]:
    patterns: list[str] = []
    if staging_policy.USE_INVENTORY_IGNORE:
        ignore_file = inventory_root / ".inventory-ignore"
        if ignore_file.is_file():
            for line in ignore_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    if ansible_cfg and ansible_cfg.is_file():
        for raw in ansible_cfg.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*ignore_patterns\s*=\s*(.+)$", raw.strip(), re.IGNORECASE)
            if m:
                for part in m.group(1).split(","):
                    p = part.strip()
                    if p:
                        patterns.append(p)
    return patterns


def path_ignored(rel_path: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if fnmatch.fnmatch(rel_path, pat) or fnmatch.fnmatch(Path(rel_path).name, pat):
            return True
    return False


def parse_inventory_ini(text: str) -> tuple[dict[str, list[str]], dict[str, list[str]], list[str]]:
    hosts_by_group: dict[str, list[str]] = {}
    children_by_group: dict[str, list[str]] = {}
    section_order: list[tuple[str, str]] = []
    current: str | None = None
    current_kind = "hosts"
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            header = line[1:-1].strip()
            if ":" in header:
                group, kind = header.split(":", 1)
                current = group.strip()
                current_kind = kind.strip()
            else:
                current = header
                current_kind = "hosts"
            section_order.append((current, current_kind))
            hosts_by_group.setdefault(current, [])
            children_by_group.setdefault(current, [])
            continue
        if not current:
            continue
        token = line.split()[0]
        if current_kind == "children":
            children_by_group.setdefault(current, []).append(token)
        else:
            hosts_by_group.setdefault(current, []).append(token)
    merge_order = [f"{g}:{k}" for g, k in section_order]
    return hosts_by_group, children_by_group, merge_order


def hosts_for_group(
    group: str,
    hosts_by_group: dict[str, list[str]],
    children_by_group: dict[str, list[str]],
    memo: dict[str, set[str]],
) -> set[str]:
    if group in memo:
        return memo[group]
    hosts = set(hosts_by_group.get(group, []))
    for child in children_by_group.get(group, []):
        hosts |= hosts_for_group(child, hosts_by_group, children_by_group, memo)
    memo[group] = hosts
    return hosts


def group_depth(
    group: str,
    children_by_group: dict[str, list[str]],
    memo: dict[str, int],
) -> int:
    if group in memo:
        return memo[group]
    depth = 0
    for parent, kids in children_by_group.items():
        if group in kids:
            depth = max(depth, group_depth(parent, children_by_group, memo) + 1)
    memo[group] = depth
    return depth


def host_groups(
    hostname: str,
    hosts_by_group: dict[str, list[str]],
    children_by_group: dict[str, list[str]],
    children_first: bool,
) -> list[str]:
    direct: list[str] = []
    for group, hosts in hosts_by_group.items():
        if hostname in hosts:
            direct.append(group)
    all_groups: set[str] = set(direct)
    if children_first:
        for g in direct:
            for parent, kids in children_by_group.items():
                if g in kids:
                    all_groups.add(parent)
    else:
        all_groups = set(direct)
    depth_memo: dict[str, int] = {}
    ordered = sorted(all_groups, key=lambda g: (group_depth(g, children_by_group, depth_memo), g))
    if "all" in ordered:
        ordered = ["all"] + [g for g in ordered if g != "all"]
    else:
        ordered = ["all", *ordered]
    return ordered


def collect_hosts(
    hosts_by_group: dict[str, list[str]], children_by_group: dict[str, list[str]]
) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for hosts in hosts_by_group.values():
        for h in hosts:
            if h not in seen:
                seen.add(h)
                ordered.append(h)
    return sorted(ordered)


def load_vars_file(
    inventory_root: Path, rel: str, patterns: list[str]
) -> tuple[dict[str, str], bool]:
    if path_ignored(rel, patterns):
        return {}, True
    path = inventory_root / rel
    return load_simple_yaml(path), False


def effective_vars_for_host(
    inventory_root: Path,
    hostname: str,
    hosts_by_group: dict[str, list[str]],
    children_by_group: dict[str, list[str]],
    patterns: list[str],
    children_first: bool,
    host_before_groups: bool,
) -> tuple[dict[str, str], dict[str, str]]:
    groups = host_groups(hostname, hosts_by_group, children_by_group, children_first)
    effective: dict[str, str] = {}
    sources: dict[str, str] = {}
    group_files = [(g, f"group_vars/{g}.yml") for g in groups]
    host_file = f"host_vars/{hostname}.yml"
    if host_before_groups:
        ordered_files: list[tuple[str, str]] = [("host", host_file)] + [
            ("group", p) for _, p in group_files
        ]
    else:
        ordered_files = [("group", p) for _, p in group_files] + [("host", host_file)]
    for _kind, rel in ordered_files:
        data, ignored = load_vars_file(inventory_root, rel, patterns)
        if ignored:
            continue
        for key, val in data.items():
            effective[key] = val
            sources[key] = rel
    return effective, sources


def reference_effective_vars(
    inventory_root: Path,
    hostname: str,
    hosts_by_group: dict[str, list[str]],
    children_by_group: dict[str, list[str]],
    patterns: list[str],
) -> dict[str, str]:
    children_first, host_before_groups = group_policy.host_group_flags()
    eff, _ = effective_vars_for_host(
        inventory_root,
        hostname,
        hosts_by_group,
        children_by_group,
        patterns,
        children_first=children_first,
        host_before_groups=host_before_groups,
    )
    return eff


def scan_findings(
    inventory_root: Path,
    hosts: list[str],
    hosts_by_group: dict[str, list[str]],
    children_by_group: dict[str, list[str]],
    patterns: list[str],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    children_first, host_before_groups = group_policy.host_group_flags()
    for host in hosts:
        eff, sources = effective_vars_for_host(
            inventory_root,
            host,
            hosts_by_group,
            children_by_group,
            patterns,
            children_first=children_first,
            host_before_groups=host_before_groups,
        )
        for key, val in eff.items():
            src = sources.get(key, "")
            if is_secret_key(key) and not is_vault_value(val):
                findings.append(
                    {
                        "category": "plaintext_secret",
                        "host": host,
                        "var_key": key,
                        "severity": SEVERITY_WEIGHTS["plaintext_secret"],
                        "source_path": str(inventory_root / src) if src else "",
                    }
                )
        layer_values: dict[str, dict[str, str]] = {}
        for g in host_groups(host, hosts_by_group, children_by_group, children_first):
            rel = f"group_vars/{g}.yml"
            if path_ignored(rel, patterns):
                continue
            gdata = load_simple_yaml(inventory_root / rel)
            if gdata:
                layer_values[g] = gdata
        keys_seen: set[str] = set()
        for gdata in layer_values.values():
            keys_seen |= set(gdata)
        for key in keys_seen:
            vals = {g: gdata[key] for g, gdata in layer_values.items() if key in gdata}
            if len(vals) > 1 and len(set(vals.values())) > 1:
                findings.append(
                    {
                        "category": "precedence_shadow",
                        "host": host,
                        "var_key": key,
                        "severity": SEVERITY_WEIGHTS["precedence_shadow"],
                        "source_path": f"group_vars/{list(vals)[-1]}.yml",
                    }
                )
        group_vault: dict[str, str] = {}
        for g in host_groups(host, hosts_by_group, children_by_group, children_first):
            gpath = inventory_root / f"group_vars/{g}.yml"
            if gpath.is_file() and not path_ignored(f"group_vars/{g}.yml", patterns):
                for k, v in load_simple_yaml(gpath).items():
                    if is_vault_value(v):
                        group_vault[k] = v
        for key, val in eff.items():
            if key in group_vault and is_vault_value(group_vault[key]) and not is_vault_value(val):
                findings.append(
                    {
                        "category": "vault_exposure",
                        "host": host,
                        "var_key": key,
                        "severity": SEVERITY_WEIGHTS["vault_exposure"],
                        "source_path": str(inventory_root / sources.get(key, "")),
                    }
                )

    for rel_path in sorted(inventory_root.rglob("*.yml")):
        rel = str(rel_path.relative_to(inventory_root)).replace("\\", "/")
        if not path_ignored(rel, patterns):
            continue
        for key, val in load_simple_yaml(rel_path).items():
            if is_secret_key(key) and not is_vault_value(val):
                findings.append(
                    {
                        "category": "ignored_file_leak",
                        "host": "*",
                        "var_key": key,
                        "severity": SEVERITY_WEIGHTS["ignored_file_leak"],
                        "source_path": str(rel_path),
                    }
                )

    dedup: dict[tuple[str, str, str], dict[str, Any]] = {}
    for f in findings:
        dedup[(f["category"], f["host"], f["var_key"])] = f
    out = list(dedup.values())
    out.sort(key=lambda f: (f["category"], f["host"], f["var_key"]))
    return out


def build_scan_snapshot(manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tree_id = manifest["tree_id"]
    inventory_root = Path(manifest["inventory_root"])
    ansible_cfg = Path(manifest.get("ansible_cfg", inventory_root / "ansible.cfg"))
    hosts_ini = inventory_root / "hosts.ini"
    if not hosts_ini.is_file():
        hosts_ini = inventory_root / "inventory" / "hosts.ini"
    ini_text = hosts_ini.read_text(encoding="utf-8")
    hosts_by_group, children_by_group, merge_order = parse_inventory_ini(ini_text)
    hosts = collect_hosts(hosts_by_group, children_by_group)
    patterns = load_ignore_patterns(inventory_root, ansible_cfg)
    host_rows: list[dict[str, Any]] = []
    children_first, host_before_groups = group_policy.host_group_flags()
    for host in hosts:
        groups = host_groups(host, hosts_by_group, children_by_group, children_first=children_first)
        eff, _ = effective_vars_for_host(
            inventory_root,
            host,
            hosts_by_group,
            children_by_group,
            patterns,
            children_first=children_first,
            host_before_groups=host_before_groups,
        )
        host_rows.append({"host": host, "groups": groups, "effective_vars": eff})
    findings = scan_findings(
        inventory_root, hosts, hosts_by_group, children_by_group, patterns
    )
    staging_digest = staging_policy.compute_staging_digest(host_rows, findings)
    fp = tree_fingerprint(manifest_path, inventory_root)
    return {
        "tree_id": tree_id,
        "tree_fingerprint": fp,
        "staging_digest": staging_digest,
        "merge_order": merge_order,
        "host_count": len(hosts),
        "finding_count": len(findings),
        "hosts": host_rows,
        "findings": findings,
        "inventory_root": str(inventory_root),
        "manifest_path": str(manifest_path),
    }


def summarize(findings: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        sev = f.get("severity", "low")
        if sev in summary:
            summary[sev] += 1
    return summary


def render_exposure_ledger(staging: dict[str, Any], run_seq: int = 1) -> dict[str, Any]:
    findings = staging["findings"]
    group_lineage = [{"host": row["host"], "groups": row["groups"]} for row in staging["hosts"]]
    return {
        "schema_version": "1",
        "tree_id": staging["tree_id"],
        "staging_digest": staging["staging_digest"],
        "run_seq": run_seq,
        "summary": summarize(findings),
        "findings": findings,
        "group_lineage": group_lineage,
        "merge_order": staging["merge_order"],
    }


def reload_scan_snapshot(state_dir: Path) -> dict[str, Any]:
    meta = json.loads((state_dir / "scan-manifest.json").read_text(encoding="utf-8"))
    hosts = [
        json.loads(line)
        for line in (state_dir / "host-rows.ndjson").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    findings = [
        json.loads(line)
        for line in (state_dir / "atlas-rows.ndjson")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    staging = dict(meta)
    staging["hosts"] = hosts
    staging["findings"] = findings
    return staging


# --- CLI ---

APP_ROOT = Path("/app")
STATE_DIR = APP_ROOT / "state"


def write_staging(staging: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    hosts_path = STATE_DIR / "host-rows.ndjson"
    findings_path = STATE_DIR / "atlas-rows.ndjson"
    hosts_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in staging["hosts"]) + "\n",
        encoding="utf-8",
    )
    findings_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in staging["findings"]) + "\n",
        encoding="utf-8",
    )
    meta = {
        "tree_id": staging["tree_id"],
        "tree_fingerprint": staging["tree_fingerprint"],
        "staging_digest": staging["staging_digest"],
        "merge_order": staging["merge_order"],
        "host_count": staging["host_count"],
        "finding_count": staging["finding_count"],
    }
    (STATE_DIR / "scan-manifest.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (STATE_DIR / "active-tree.id").write_text(staging["tree_id"], encoding="utf-8")


def update_run_seq(fp: str, tree_id: str) -> int:
    run_seq_file = STATE_DIR / "run-seq.json"
    if run_seq_file.is_file():
        data = json.loads(run_seq_file.read_text(encoding="utf-8"))
        run_seq = int(data.get("run_seq", 0))
        if data.get("last_tree_fingerprint") != fp:
            run_seq += 1
    else:
        run_seq = 1
    run_seq_file.write_text(
        json.dumps(
            {"run_seq": run_seq, "last_tree_fingerprint": fp, "tree_id": tree_id},
            indent=2,
        ),
        encoding="utf-8",
    )
    return run_seq


def cmd_scan(manifest: str) -> int:
    manifest_path = Path(manifest)
    if not manifest_path.is_file():
        return 2
    staging = build_scan_snapshot(manifest_path)
    write_staging(staging)
    update_run_seq(staging["tree_fingerprint"], staging["tree_id"])
    return 0


def cmd_emit(tree_id: str, output: str) -> int:
    meta_path = STATE_DIR / "scan-manifest.json"
    if not meta_path.is_file():
        return 3
    active = (STATE_DIR / "active-tree.id").read_text(encoding="utf-8").strip()
    if active != tree_id:
        return 3
    if staging_policy.EXPORT_REOPEN:
        manifest_guess = APP_ROOT / "fixtures" / "trees" / tree_id / "tree.json"
        if manifest_guess.is_file():
            cmd_scan(str(manifest_guess))
    staging = reload_scan_snapshot(STATE_DIR)
    run_seq = json.loads((STATE_DIR / "run-seq.json").read_text(encoding="utf-8"))["run_seq"]
    report = render_exposure_ledger(staging, run_seq=run_seq)
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


def main() -> int:
    import sys

    if len(sys.argv) < 2:
        return 2
    cmd = sys.argv[1]
    if cmd in ("scan", "ingest"):
        manifest = ""
        args = sys.argv[2:]
        i = 0
        while i < len(args):
            if args[i] == "--tree" and i + 1 < len(args):
                manifest = args[i + 1]
                i += 2
            else:
                i += 1
        if not manifest:
            return 2
        return cmd_scan(manifest)
    if cmd in ("emit", "export"):
        tree_id = ""
        output = ""
        args = sys.argv[2:]
        i = 0
        while i < len(args):
            if args[i] == "--tree" and i + 1 < len(args):
                tree_id = args[i + 1]
                i += 2
            elif args[i] == "--output" and i + 1 < len(args):
                output = args[i + 1]
                i += 2
            else:
                i += 1
        if not tree_id or not output:
            return 2
        return cmd_emit(tree_id, output)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
