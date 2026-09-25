"""Lineage merge helpers for Ansible inventory trees."""

from __future__ import annotations


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
