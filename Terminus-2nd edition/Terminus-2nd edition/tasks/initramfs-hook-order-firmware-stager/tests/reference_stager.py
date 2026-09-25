"""Independent reference stager for initramfs manifest export."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG = {
    "kernel_version": "6.1.0",
    "include_hook_scripts": True,
    "compression": {"default": "none", ".ko": "xz", ".bin": "gz", ".sh": "none"},
}


@dataclass(frozen=True)
class Hook:
    name: str
    order: int
    path: str
    prereqs: tuple[str, ...]


@dataclass(frozen=True)
class ManifestRow:
    path: str
    size: int
    sha256: str
    compress: str
    kind: str
    hook_rank: int


def load_config(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    merged = dict(DEFAULT_CONFIG)
    merged.update(data)
    merged["compression"] = {**DEFAULT_CONFIG["compression"], **data.get("compression", {})}
    return merged


def _read_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8-sig")
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rootfs_digest(root: Path) -> str:
    h = hashlib.sha256()
    for f in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix()):
        rel = f.relative_to(root).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(f.read_bytes())
    return h.hexdigest()


def _parse_hook_file(path: Path, rel: str) -> Hook | None:
    text = path.read_text(encoding="utf-8")
    base = path.name
    m = re.match(r"^(\d+)-(.+)\.sh$", base)
    if not m:
        return None
    order = int(m.group(1))
    default_name = m.group(2)
    hook_name = default_name
    prereqs: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# PREREQ="):
            raw = line.split("=", 1)[1].strip()
            prereqs = [p.strip() for p in raw.split(",") if p.strip()]
        elif line.startswith("# HOOK="):
            hook_name = line.split("=", 1)[1].strip()
    return Hook(name=hook_name, order=order, path=rel, prereqs=tuple(prereqs))


def discover_hooks(root: Path) -> list[Hook]:
    hooks_dir = root / "hooks"
    if not hooks_dir.is_dir():
        return []
    hooks: list[Hook] = []
    for path in sorted(hooks_dir.glob("*.sh")):
        rel = path.relative_to(root).as_posix()
        hook = _parse_hook_file(path, rel)
        if hook:
            hooks.append(hook)
    return hooks


def topo_sort_hooks(hooks: list[Hook]) -> list[Hook]:
    by_name = {h.name: h for h in hooks}
    missing = {p for h in hooks for p in h.prereqs if p not in by_name}
    if missing:
        raise ValueError(f"unknown prereq: {sorted(missing)}")

    indeg = {h.name: 0 for h in hooks}
    children: dict[str, list[str]] = {h.name: [] for h in hooks}
    for h in hooks:
        for p in h.prereqs:
            indeg[h.name] += 1
            children[p].append(h.name)

    ready = [h for h in hooks if indeg[h.name] == 0]
    order: list[Hook] = []
    while ready:
        ready.sort(key=lambda h: (h.order, h.name))
        cur = ready.pop(0)
        order.append(cur)
        for child_name in children[cur.name]:
            indeg[child_name] -= 1
            if indeg[child_name] == 0:
                ready.append(by_name[child_name])
    if len(order) != len(hooks):
        raise ValueError("cycle")
    return order


def _glob_match(pattern: str, value: str) -> bool:
    return fnmatch.fnmatchcase(value, pattern)


def parse_alias_lines(alias_path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    if not alias_path.is_file():
        return rows
    for line in alias_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "alias":
            rows.append((parts[1], parts[2]))
    return rows


def select_modules(root: Path, kver: str) -> list[str]:
    load_path = root / "etc" / "irfs" / "modules.load"
    pci_path = root / "etc" / "irfs" / "pci.ids"
    alias_path = root / "lib" / "modules" / kver / "modules.alias"
    requested = _read_lines(load_path)
    pci_ids = _read_lines(pci_path)
    aliases = parse_alias_lines(alias_path)
    selected: list[str] = []
    for mod in requested:
        matched = False
        for pattern, modname in aliases:
            if modname != mod:
                continue
            if any(_glob_match(pattern, pci) for pci in pci_ids):
                matched = True
                break
        if matched:
            selected.append(mod)
    return selected


def module_ko_paths(root: Path, kver: str, module: str) -> list[Path]:
    base = root / "lib" / "modules" / kver
    if not base.is_dir():
        return []
    hits = sorted(base.rglob(f"{module}.ko"), key=lambda p: p.relative_to(root).as_posix())
    return hits


def firmware_paths(root: Path, modules: list[str]) -> list[tuple[str, Path]]:
    fmap = root / "etc" / "irfs" / "firmware.map"
    if not fmap.is_file():
        return []
    out: list[tuple[str, Path]] = []
    modset = set(modules)
    for line in _read_lines(fmap):
        parts = line.split()
        if len(parts) < 2:
            continue
        mod, rel = parts[0], parts[1]
        if mod not in modset:
            continue
        fw = root / "lib" / "firmware" / rel
        if fw.is_file():
            out.append((mod, fw))
    return out


def compress_tag(path: str, cfg: dict) -> str:
    comp = cfg.get("compression", DEFAULT_CONFIG["compression"])
    default = comp.get("default", "none")
    suffix = Path(path).suffix.lower()
    return comp.get(suffix, default)


def _hook_rank_by_name(order: list[Hook]) -> dict[str, int]:
    return {h.name: idx + 1 for idx, h in enumerate(order)}


def _owner_rank(hook_ranks: dict[str, int], *candidates: str) -> int:
    for name in candidates:
        if name in hook_ranks:
            return hook_ranks[name]
    return 1


def build_manifest_rows(root: Path, cfg: dict) -> tuple[list[ManifestRow], list[Hook]]:
    kver = cfg["kernel_version"]
    hooks = discover_hooks(root)
    hook_order = topo_sort_hooks(hooks)
    hook_ranks = _hook_rank_by_name(hook_order)
    modules = select_modules(root, kver)
    firmware = firmware_paths(root, modules)
    rows: list[ManifestRow] = []

    if cfg.get("include_hook_scripts", True):
        for h in hook_order:
            src = root / h.path
            rows.append(
                ManifestRow(
                    path=h.path,
                    size=src.stat().st_size,
                    sha256=_file_digest(src),
                    compress=compress_tag(h.path, cfg),
                    kind="hook",
                    hook_rank=hook_ranks[h.name],
                )
            )

    mod_rank = _owner_rank(hook_ranks, "modules", "modprobe")
    for mod in modules:
        for ko in module_ko_paths(root, kver, mod):
            rel = ko.relative_to(root).as_posix()
            rows.append(
                ManifestRow(
                    path=rel,
                    size=ko.stat().st_size,
                    sha256=_file_digest(ko),
                    compress=compress_tag(rel, cfg),
                    kind="module",
                    hook_rank=mod_rank,
                )
            )

    fw_rank = _owner_rank(hook_ranks, "firmware", "modules")
    for _mod, fw in firmware:
        rel = fw.relative_to(root).as_posix()
        rows.append(
            ManifestRow(
                path=rel,
                size=fw.stat().st_size,
                sha256=_file_digest(fw),
                compress=compress_tag(rel, cfg),
                kind="firmware",
                hook_rank=fw_rank,
            )
        )

    rows.sort(key=lambda r: r.path)
    return rows, hook_order


def render_manifest(rows: list[ManifestRow]) -> str:
    lines = [
        f"{r.path}\t{r.size}\t{r.sha256}\t{r.compress}\t{r.kind}\t{r.hook_rank}" for r in rows
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def stage_rootfs(root: Path, cfg: dict) -> tuple[str, list[Hook]]:
    rows, hook_order = build_manifest_rows(root, cfg)
    return render_manifest(rows), hook_order


def manifest_for_run(root: Path, ledger: Path, hook_order: list[Hook]) -> dict:
    ledger_bytes = ledger.read_bytes() if ledger.is_file() else b""
    lines = [ln for ln in ledger_bytes.decode("utf-8").splitlines() if ln.strip()]
    return {
        "rootfs_sha256": rootfs_digest(root),
        "entry_count": len(lines),
        "ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
        "hook_order": [h.name for h in hook_order],
    }


def build_seed_rootfs(seed: str) -> dict[str, str]:
    """Synthetic mini rootfs layout keyed by relative path for anti-hardcoding."""
    h = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16)
    mod = f"seedmod{h % 97}"
    blob = f"seed-fw-{h % 1000}"
    return {
        "hooks/10-base.sh": "#!/bin/sh\n# PREREQ=\necho base\n",
        f"hooks/20-{mod}.sh": "#!/bin/sh\n# PREREQ=base\n# HOOK=modules\necho mod\n",
        "hooks/30-firmware.sh": "#!/bin/sh\n# PREREQ=modules\necho fw\n",
        "etc/irfs/modules.load": f"{mod}\n",
        "etc/irfs/pci.ids": f"pci:v0000SEEDd{h % 9999:04x}*\n",
        "etc/irfs/firmware.map": f"{mod} vendor/{blob}.bin\n",
        "lib/modules/6.1.0/modules.alias": f"alias pci:v0000SEEDd{h % 9999:04x}* {mod}\n",
        f"lib/modules/6.1.0/kernel/drivers/net/{mod}.ko": f"KO-{seed}-{h}\n",
        f"lib/firmware/vendor/{blob}.bin": f"BIN-{seed}-{h}\n",
    }


def write_seed_rootfs(tmp: Path, seed: str) -> Path:
    root = tmp / "seed-rootfs"
    root.mkdir(parents=True, exist_ok=True)
    for rel, content in build_seed_rootfs(seed).items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
    return root


def build_seed_input(seed: str) -> Path:
    raise RuntimeError("use write_seed_rootfs with TemporaryDirectory")
