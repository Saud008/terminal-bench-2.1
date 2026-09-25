"""Independent verifier oracle for ldaprm LDAP effective rights matrix."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCOPE_WEIGHT = {"entry": 300, "one": 200, "subtree": 100}


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_dn(dn: str) -> str:
    parts: list[str] = []
    for rdn in dn.split(","):
        rdn = rdn.strip()
        if not rdn:
            continue
        if "=" in rdn:
            attr, val = rdn.split("=", 1)
            parts.append(f"{attr.strip().lower()}={val.strip()}")
        else:
            parts.append(rdn.lower())
    return ",".join(parts)


def dn_depth(dn: str) -> int:
    return len([p for p in normalize_dn(dn).split(",") if p])


def is_child(parent: str, child: str) -> bool:
    p = normalize_dn(parent)
    c = normalize_dn(child)
    return c != p and c.endswith("," + p)


def is_direct_child(parent: str, child: str) -> bool:
    if not is_child(parent, child):
        return False
    return dn_depth(parent) + 1 == dn_depth(child)


def scope_matches(scope: str, ace_target: str, entry_dn: str) -> bool:
    ace_t = normalize_dn(ace_target)
    entry = normalize_dn(entry_dn)
    if scope == "entry":
        return entry == ace_t
    if scope == "one":
        return entry == ace_t or is_direct_child(ace_t, entry)
    if scope == "subtree":
        return entry == ace_t or is_child(ace_t, entry)
    return False


def parse_ldif_entries(ldif_path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    cur_dn = ""
    cur_classes: list[str] = []
    for line in ldif_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("dn:"):
            if cur_dn:
                entries.append({"dn": normalize_dn(cur_dn), "object_classes": sorted(set(cur_classes))})
            cur_dn = line[3:].strip()
            cur_classes = []
        elif line.startswith("objectClass:"):
            cur_classes.append(line.split(":", 1)[1].strip())
        elif line.strip() == "" and cur_dn:
            entries.append({"dn": normalize_dn(cur_dn), "object_classes": sorted(set(cur_classes))})
            cur_dn = ""
            cur_classes = []
    if cur_dn:
        entries.append({"dn": normalize_dn(cur_dn), "object_classes": sorted(set(cur_classes))})
    entries.sort(key=lambda e: e["dn"])
    return entries


def parse_groups_tsv(groups_path: Path) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    for line in groups_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        group, member = line.split("\t", 1)
        g = normalize_dn(group.strip())
        m = normalize_dn(member.strip())
        graph.setdefault(g, set()).add(m)
    return graph


def expand_groups(graph: dict[str, set[str]]) -> dict[str, set[str]]:
    """Transitive closure: each group maps to all member DNs including nested groups."""
    cache: dict[str, set[str]] = {}

    def members_of(node: str, stack: set[str]) -> set[str]:
        if node in cache:
            return cache[node]
        if node in stack:
            return set()
        stack = set(stack)
        stack.add(node)
        out: set[str] = set()
        for m in graph.get(node, set()):
            if m in graph:
                out |= members_of(m, stack)
            else:
                out.add(m)
        cache[node] = out
        return out

    for g in list(graph.keys()):
        members_of(g, set())
    return cache


def parse_acl_rule_line(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line.startswith(("ALLOW ", "DENY ")):
        return None
    effect = "allow" if line.startswith("ALLOW ") else "deny"
    body = line.split(None, 1)[1]
    if " ATTR " not in body:
        return None
    left, attrs_part = body.split(" ATTR ", 1)
    attrs = [a.strip() for a in attrs_part.split(",")]
    m = re.match(
        r"(group|user)\s+(.+?)\s+((?:read|write|search|delete|compare)(?:,(?:read|write|search|delete|compare))*)$",
        left.strip(),
        re.IGNORECASE,
    )
    if not m:
        return None
    return {
        "effect": effect,
        "subject_type": m.group(1).lower(),
        "subject_dn": normalize_dn(m.group(2).strip()),
        "rights": [r.strip() for r in m.group(3).split(",")],
        "attrs": attrs,
    }


def parse_acl_dir(acl_dir: Path) -> list[dict[str, Any]]:
    aces: list[dict[str, Any]] = []
    ace_id = 0
    for f in sorted(acl_dir.glob("*.acl")):
        block: dict[str, Any] = {"rules": []}
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line == "---":
                if block.get("target"):
                    aces.append(_finalize_ace(block, ace_id, f.stem))
                    ace_id += 1
                    block = {"rules": []}
                continue
            if line.startswith("TARGET "):
                block["target"] = line[7:].strip()
            elif line.startswith("SCOPE "):
                block["scope"] = line[6:].strip().lower()
            elif line.startswith("INHERIT "):
                block["inherit"] = line[8:].strip().lower()
            else:
                rule = parse_acl_rule_line(line)
                if rule:
                    block.setdefault("rules", []).append(rule)
        if block.get("target"):
            aces.append(_finalize_ace(block, ace_id, f.stem))
            ace_id += 1
    return aces


def _finalize_ace(block: dict[str, Any], ace_id: int, source: str) -> dict[str, Any]:
    target = normalize_dn(block.get("target", ""))
    scope = block.get("scope", "subtree").lower()
    inherit = block.get("inherit", "yes").lower() in ("yes", "true", "1")
    rules = block.get("rules", [])
    flat: list[dict[str, Any]] = []
    for i, r in enumerate(rules):
        flat.append(
            {
                "ace_id": f"{source}:{ace_id}:{i}",
                "target": target,
                "scope": scope,
                "inherit": inherit,
                **r,
            }
        )
    return {"target": target, "scope": scope, "inherit": inherit, "rules": flat, "source": source}


def flatten_aces(acl_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for block in acl_blocks:
        out.extend(block["rules"])
    return out


def load_defaults(defaults_path: Path) -> dict[str, Any]:
    return json.loads(defaults_path.read_text(encoding="utf-8"))


def subject_in_group(subject: str, group_dn: str, closure: dict[str, set[str]], graph: dict[str, set[str]]) -> bool:
    subj = normalize_dn(subject)
    grp = normalize_dn(group_dn)
    if subj == grp:
        return True
    if grp in closure:
        return subj in closure[grp]
    return subj in graph.get(grp, set())


def ace_rank(ace: dict[str, Any]) -> tuple[int, int, int, int, str]:
    depth = dn_depth(ace["target"])
    scope_w = SCOPE_WEIGHT.get(ace["scope"], 0)
    user_first = 0 if ace["subject_type"] == "user" else 1
    deny_first = 0 if ace["effect"] == "deny" else 1
    return (-depth, -scope_w, user_first, deny_first, ace["ace_id"])


def attr_matches(ace_attrs: list[str], attr: str) -> bool:
    if "*" in ace_attrs:
        return True
    return attr.lower() in [a.lower() for a in ace_attrs]


def collect_applicable_aces(
    entry_dn: str,
    subject_dn: str,
    flat_aces: list[dict[str, Any]],
    closure: dict[str, set[str]],
    graph: dict[str, set[str]],
) -> list[dict[str, Any]]:
    applicable: list[dict[str, Any]] = []
    entry = normalize_dn(entry_dn)
    for ace in flat_aces:
        if not scope_matches(ace["scope"], ace["target"], entry):
            continue
        if ace["subject_type"] == "user":
            if normalize_dn(subject_dn) != ace["subject_dn"]:
                continue
        elif not subject_in_group(subject_dn, ace["subject_dn"], closure, graph):
            continue
        applicable.append(dict(ace))
    applicable.sort(key=ace_rank)
    return applicable


def inherit_blocked(flat_aces: list[dict[str, Any]], entry_dn: str) -> bool:
    entry = normalize_dn(entry_dn)
    for ace in flat_aces:
        if normalize_dn(ace["target"]) == entry and not ace.get("inherit", True):
            return True
    return False


def default_rights_for_entry(
    entry_dn: str,
    entries: list[dict[str, Any]],
    defaults: dict[str, Any],
    flat_aces: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    if inherit_blocked(flat_aces, entry_dn):
        return []
    entry = normalize_dn(entry_dn)
    obj_classes: list[str] = []
    for e in entries:
        if e["dn"] == entry:
            obj_classes = e["object_classes"]
            break
    rights: list[tuple[str, str]] = []
    by_oc = defaults.get("by_objectclass", {})
    for oc in obj_classes:
        spec = by_oc.get(oc, {})
        for right in spec.get("rights", []):
            for attr in spec.get("attrs", ["*"]):
                rights.append((right, attr))
    return rights


def decide_probe(
    probe: dict[str, Any],
    entries: list[dict[str, Any]],
    flat_aces: list[dict[str, Any]],
    closure: dict[str, set[str]],
    graph: dict[str, set[str]],
    defaults: dict[str, Any],
) -> dict[str, Any]:
    pid = probe["probe_id"]
    subject = normalize_dn(probe["subject_dn"])
    entry = normalize_dn(probe["entry_dn"])
    attr = probe["attribute"]
    right = probe["right"]

    applicable = collect_applicable_aces(entry, subject, flat_aces, closure, graph)

    winning = ""
    for ace in applicable:
        if right not in ace["rights"]:
            continue
        if not attr_matches(ace["attrs"], attr):
            continue
        if ace["effect"] == "deny":
            ad = sha256_hex(f"{pid}|deny|ace_deny|{ace['ace_id']}|{entry}")
            return {
                "probe_id": pid,
                "subject_dn": subject,
                "entry_dn": entry,
                "attribute": attr,
                "right": right,
                "verdict": "deny",
                "reason": "ace_deny",
                "winning_ace_id": ace["ace_id"],
                "audit_digest": ad,
            }
        winning = ace["ace_id"]
        ad = sha256_hex(f"{pid}|allow|ace_allow|{winning}|{entry}")
        return {
            "probe_id": pid,
            "subject_dn": subject,
            "entry_dn": entry,
            "attribute": attr,
            "right": right,
            "verdict": "allow",
            "reason": "ace_allow",
            "winning_ace_id": winning,
            "audit_digest": ad,
        }

    for dr, da in default_rights_for_entry(entry, entries, defaults, flat_aces):
        if dr != right:
            continue
        if da != "*" and da.lower() != attr.lower():
            continue
        ad = sha256_hex(f"{pid}|allow|default_inherit||{entry}")
        return {
            "probe_id": pid,
            "subject_dn": subject,
            "entry_dn": entry,
            "attribute": attr,
            "right": right,
            "verdict": "allow",
            "reason": "default_inherit",
            "winning_ace_id": "",
            "audit_digest": ad,
        }

    ad = sha256_hex(f"{pid}|deny|no_match||{entry}")
    return {
        "probe_id": pid,
        "subject_dn": subject,
        "entry_dn": entry,
        "attribute": attr,
        "right": right,
        "verdict": "deny",
        "reason": "no_match",
        "winning_ace_id": "",
        "audit_digest": ad,
    }


def staging_fingerprint(entries: list, flat_aces: list, closure: dict, defaults: dict) -> str:
    lines: list[str] = []
    for e in entries:
        lines.append(f"entry;{e['dn']};{','.join(e['object_classes'])}")
    for ace in sorted(flat_aces, key=lambda a: a["ace_id"]):
        lines.append(
            f"ace;{ace['ace_id']};{ace['target']};{ace['scope']};{int(ace.get('inherit', True))};"
            f"{ace['effect']};{ace['subject_type']};{ace['subject_dn']};{','.join(ace['rights'])};"
            f"{','.join(ace['attrs'])}"
        )
    for g in sorted(closure.keys()):
        for m in sorted(closure[g]):
            lines.append(f"member;{g};{m}")
    for oc, spec in sorted(defaults.get("by_objectclass", {}).items()):
        lines.append(f"default;{oc};{','.join(spec.get('rights', []))};{','.join(spec.get('attrs', ['*']))}")
    return sha256_hex("\n".join(lines))


def build_staging(
    ldif: Path,
    groups: Path,
    acl_dir: Path,
    defaults_path: Path,
) -> dict[str, Any]:
    entries = parse_ldif_entries(ldif)
    graph = parse_groups_tsv(groups)
    closure = expand_groups(graph)
    acl_blocks = parse_acl_dir(acl_dir)
    flat = flatten_aces(acl_blocks)
    defaults = load_defaults(defaults_path)
    fp = staging_fingerprint(entries, flat, closure, defaults)
    return {
        "schema_version": 1,
        "entries": entries,
        "group_graph": {k: sorted(v) for k, v in graph.items()},
        "group_closure": {k: sorted(v) for k, v in closure.items()},
        "aces": flat,
        "defaults": defaults,
        "staging_fingerprint": fp,
    }


def staging_from_paths(
    ldif: Path,
    groups: Path,
    acl_dir: Path,
    defaults_path: Path,
) -> dict[str, Any]:
    return build_staging(ldif, groups, acl_dir, defaults_path)


def build_matrix(
    staging: dict[str, Any],
    probes_doc: dict[str, Any],
    acl_dir_override: Path | None = None,
) -> dict[str, Any]:
    entries = staging["entries"]
    if acl_dir_override is not None:
        flat = flatten_aces(parse_acl_dir(acl_dir_override))
    else:
        flat = staging["aces"]
    closure = {k: set(v) for k, v in staging["group_closure"].items()}
    graph = {k: set(v) for k, v in staging["group_graph"].items()}
    defaults = staging["defaults"]
    decisions = [
        decide_probe(p, entries, flat, closure, graph, defaults) for p in probes_doc["probes"]
    ]
    decisions.sort(key=lambda d: d["probe_id"])
    digest_lines = [f"{d['probe_id']};{d['verdict']};{d['reason']};{d['winning_ace_id']}" for d in decisions]
    report_digest = sha256_hex("\n".join(digest_lines))
    return {
        "schema_version": 1,
        "staging_fingerprint": staging["staging_fingerprint"],
        "decisions": decisions,
        "report_digest": report_digest,
    }


def verifier_pipeline(
    ldif: Path,
    groups: Path,
    acl_dir: Path,
    defaults_path: Path,
    probes_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    staging = build_staging(ldif, groups, acl_dir, defaults_path)
    probes = json.loads(probes_path.read_text(encoding="utf-8"))
    matrix = build_matrix(staging, probes)
    return staging, matrix


reference_pipeline = verifier_pipeline
