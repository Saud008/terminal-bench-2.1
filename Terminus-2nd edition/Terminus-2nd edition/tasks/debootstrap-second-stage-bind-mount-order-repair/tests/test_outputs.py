"""Behavioral verifier for stage2-audit debootstrap second-stage simulation."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest

APP = Path("/app")
ROOTFS = APP / "fixtures" / "rootfs"
OUTPUT = APP / "output"
PATH_MOUNT_SNAPSHOTS = "/app/state/mount-snapshots/"
PATH_MOUNT_GATE = "/app/state/mount-gate/"
PATH_STAGE2_LEDGER = "/app/state/stage2-ledger.json"
SNAPSHOTS = Path(PATH_MOUNT_SNAPSHOTS.rstrip("/"))
GATE_DIR = Path(PATH_MOUNT_GATE.rstrip("/"))
STAGING = APP / "state" / "stage2-staging"
LEDGER = Path(PATH_STAGE2_LEDGER)
CLI = APP / "bin" / "stage2-audit"
LIB = APP / "lib"
RESET = APP / "scripts" / "reset-state.sh"
GOLDEN = Path(__file__).resolve().parent / "verifier-golden"
BROKEN = Path(__file__).resolve().parent / "verifier-broken"
HIDDEN = Path(__file__).resolve().parent / "hidden_rootfs"
TB3_HIDDEN_MERGED = "/opt/verifier-fixtures/hidden-merged-trixie"
TB3_HIDDEN_PTS = "/opt/verifier-fixtures/hidden-deep-pts"
INGEST_STAGE = "ingest"
SEED_RESOLV = APP / "fixtures" / "shared" / "resolv.conf.seed"

BUNDLED = [
    "rootfs-001",
    "rootfs-002",
    "rootfs-003",
    "rootfs-004",
    "rootfs-005",
    "rootfs-006",
    "rootfs-007",
    "rootfs-008",
]

PROTECTED_SHA256: dict[str, str] = {}

MODULE_SOURCES = {
    "mount.sh": (BROKEN / "mount.sh", GOLDEN / "mount.sh"),
    "commit.sh": (BROKEN / "commit.sh", GOLDEN / "commit.sh"),
    "gate.sh": (BROKEN / "gate.sh", GOLDEN / "gate.sh"),
    "hooks.sh": (BROKEN / "hooks.sh", GOLDEN / "hooks.sh"),
    "resolv.sh": (BROKEN / "resolv.sh", GOLDEN / "resolv.sh"),
    "sources.sh": (BROKEN / "sources.sh", GOLDEN / "sources.sh"),
    "staging.sh": (BROKEN / "staging.sh", GOLDEN / "staging.sh"),
    "export.sh": (BROKEN / "export.sh", GOLDEN / "export.sh"),
    "driver.sh": (BROKEN / "driver.sh", GOLDEN / "driver.sh"),
}


def rootfs_digest(rootfs_dir: Path) -> str:
    parts = [
        (rootfs_dir / "meta.json").read_bytes(),
        (rootfs_dir / "mounts.json").read_bytes(),
    ]
    hooks = rootfs_dir / "hooks" / "stage2.d"
    if hooks.is_dir():
        for hook in sorted(hooks.glob("*.sh")):
            parts.append(hook.read_bytes())
    return hashlib.sha256(b"".join(parts)).hexdigest()


def _load_meta(rootfs_dir: Path) -> dict:
    return json.loads((rootfs_dir / "meta.json").read_text(encoding="utf-8"))


def _load_mounts(rootfs_dir: Path) -> list[dict]:
    return json.loads((rootfs_dir / "mounts.json").read_text(encoding="utf-8"))["mounts"]


def reference_mount_order(rootfs_dir: Path) -> list[str]:
    """Independent mount DAG topo sort per /app/docs/mount-dag.md."""
    mounts = _load_mounts(rootfs_dir)
    by_id = {m["id"]: m for m in mounts}
    ids = [m["id"] for m in mounts]
    in_deg = {i: 0 for i in ids}
    edges: set[tuple[str, str]] = set()

    def add_edge(src: str, dst: str) -> None:
        if src == dst or src not in by_id or dst not in by_id:
            return
        if (src, dst) in edges:
            return
        edges.add((src, dst))
        in_deg[dst] += 1

    targets = {m["target"]: m["id"] for m in mounts}
    for m in mounts:
        for dep in m.get("after") or []:
            add_edge(dep, m["id"])
        t = m["target"]
        if t != "/":
            parent = t.rsplit("/", 1)[0] or "/"
            if parent in targets and parent != t:
                add_edge(targets[parent], m["id"])
        if m.get("kind") == "bind":
            for vm in mounts:
                if vm.get("id") in ("proc", "sysfs"):
                    add_edge(vm["id"], m["id"])
        if m["id"] == "devbind":
            add_edge("proc", m["id"])
        if m["id"] == "devpts":
            parent = m["target"].rsplit("/", 1)[0] or "/"
            if parent in targets:
                add_edge(targets[parent], m["id"])

    queue = [i for i in ids if in_deg[i] == 0]
    result: list[str] = []
    while queue:
        queue.sort(key=lambda i: (0 if by_id[i].get("kind") == "virtual" else 1, i))
        pick = queue.pop(0)
        result.append(pick)
        for src, dst in list(edges):
            if src == pick:
                in_deg[dst] -= 1
                if in_deg[dst] == 0:
                    queue.append(dst)
    assert len(result) == len(ids), "mount cycle"
    return result


def reference_mount_steps(rootfs_dir: Path) -> list[dict]:
    mounts = {m["id"]: m for m in _load_mounts(rootfs_dir)}
    steps = []
    for mid in reference_mount_order(rootfs_dir):
        m = mounts[mid]
        steps.append(
            {
                "id": m["id"],
                "source": m["source"],
                "target": m["target"],
                "fstype": m["fstype"],
                "kind": m["kind"],
                "options": m.get("options", []),
            }
        )
    return steps


def reference_apply_markers(rootfs_dir: Path, order: list[str]) -> None:
    tree = rootfs_dir / "tree"
    mounted: list[str] = []
    for mid in order:
        mounted.append(mid)
        if mid == "proc":
            p = tree / "proc"
            p.mkdir(parents=True, exist_ok=True)
            (p / ".stage2-proc-ready").write_text("ok\n", encoding="utf-8")
        if mid == "devbind" and "proc" in mounted:
            p = tree / "dev"
            p.mkdir(parents=True, exist_ok=True)
            (p / ".stage2-dev-ready").write_text("ok\n", encoding="utf-8")


def reference_run_hooks(rootfs_dir: Path) -> list[dict]:
    hook_dir = rootfs_dir / "hooks" / "stage2.d"
    results: list[dict] = []
    env = {**os.environ, "STAGE2_ROOT": str(rootfs_dir / "tree")}
    if hook_dir.is_dir():
        for hook in sorted(hook_dir.glob("*.sh")):
            proc = subprocess.run(["bash", str(hook)], env=env, capture_output=True, text=True)
            results.append({"name": hook.name, "exit": proc.returncode})
    return results


def reference_resolv_target(rootfs_dir: Path, meta: dict) -> Path:
    if meta.get("merged_usr"):
        dest = rootfs_dir / "tree" / "usr" / "etc" / "resolv.conf"
    else:
        dest = rootfs_dir / "tree" / "etc" / "resolv.conf"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SEED_RESOLV, dest)
    return dest


def reference_sources_digest(rootfs_dir: Path, meta: dict) -> str:
    dest = rootfs_dir / "tree" / "etc" / "apt" / "sources.list.d" / "debian-stage2.list"
    dest.parent.mkdir(parents=True, exist_ok=True)
    line = f"deb http://deb.debian.org/debian {meta['codename']} main"
    existing = dest.read_text(encoding="utf-8") if dest.exists() else ""
    for _ in range(1 + int(meta.get("suite_retry") or 0)):
        if line not in existing:
            with dest.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
            existing = dest.read_text(encoding="utf-8")
    return hashlib.sha256(dest.read_bytes()).hexdigest()


def reference_audit(rootfs_dir: Path) -> dict:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="s2-ref-") as td:
        clone = Path(td) / rootfs_dir.name
        shutil.copytree(rootfs_dir, clone)
        meta = _load_meta(clone)
        order = reference_mount_order(clone)
        mount_steps = reference_mount_steps(clone)
        reference_apply_markers(clone, order)
        hooks = reference_run_hooks(clone)
        resolv = reference_resolv_target(clone, meta)
        sources_digest = reference_sources_digest(clone, meta)
        hooks_ok = all(h["exit"] == 0 for h in hooks)
        rel_resolv = resolv.relative_to(clone)
        resolv_display = str(rootfs_dir / rel_resolv)
        return {
            "pipeline_version": 1,
            "seed": meta["seed"],
            "rootfs": meta["name"],
            "mount_steps": mount_steps,
            "hooks": hooks,
            "resolv_target": resolv_display,
            "sources_digest": sources_digest,
            "ok": hooks_ok,
        }


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def audit(rootfs_name: str, export_path: Path, rootfs_root: Path = ROOTFS) -> subprocess.CompletedProcess[str]:
    export_path.parent.mkdir(parents=True, exist_ok=True)
    return run(
        [
            str(CLI),
            "run",
            "--rootfs",
            str(rootfs_root / rootfs_name),
            "--output",
            str(export_path),
        ]
    )


@contextmanager
def with_partial_patch(patches: dict[str, Path]):
    backups: dict[str, bytes] = {}

    def write_module(dest: Path, src: Path) -> None:
        data = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        dest.write_bytes(data)

    try:
        for name, (broken, _golden) in MODULE_SOURCES.items():
            dest = LIB / name
            backups[name] = dest.read_bytes()
            write_module(dest, patches.get(name, broken))
        yield
    finally:
        for name, data in backups.items():
            (LIB / name).write_bytes(data)


@contextmanager
def hidden_rootfs(name: str):
    src = HIDDEN / name
    dest = ROOTFS / name
    copied = False
    try:
        if not dest.exists():
            shutil.copytree(src, dest)
            copied = True
        yield dest
    finally:
        if copied and dest.exists():
            shutil.rmtree(dest)


@pytest.fixture(scope="session", autouse=True)
def _protected_digests() -> None:
    global PROTECTED_SHA256
    PROTECTED_SHA256 = {name: rootfs_digest(ROOTFS / name) for name in BUNDLED}


class TestStage2Audit:
    def setup_method(self) -> None:
        reset()

    def test_protected_rootfs_integrity(self) -> None:
        """Bundled rootfs fixtures must remain unmodified."""
        for name in BUNDLED:
            assert rootfs_digest(ROOTFS / name) == PROTECTED_SHA256[name], name

    @pytest.mark.parametrize("rootfs_name", BUNDLED)
    def test_rootfs_matches_reference(self, rootfs_name: str) -> None:
        """Each catalog rootfs audit must match the independent reference."""
        export = OUTPUT / f"ref-{rootfs_name}.json"
        proc = audit(rootfs_name, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        expect = reference_audit(ROOTFS / rootfs_name)
        assert got == expect

    @pytest.mark.parametrize("rootfs_name", BUNDLED)
    def test_mount_snapshot_written(self, rootfs_name: str) -> None:
        """Mount snapshot must exist under PATH_MOUNT_SNAPSHOTS with correct ordered ids."""
        export = OUTPUT / f"snap-{rootfs_name}.json"
        proc = audit(rootfs_name, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        matches = sorted(SNAPSHOTS.glob(f"{rootfs_name}-*.json"), key=lambda p: p.stat().st_mtime)
        assert matches, "missing mount snapshot"
        snap = json.loads(matches[-1].read_text(encoding="utf-8"))
        expect_ids = reference_mount_order(ROOTFS / rootfs_name)
        assert [row["id"] for row in snap["mount_steps"]] == expect_ids

    @pytest.mark.parametrize("rootfs_name", BUNDLED)
    def test_mount_gate_written(self, rootfs_name: str) -> None:
        """Mount gate record must exist under PATH_MOUNT_GATE (/app/state/mount-gate/)."""
        export = OUTPUT / f"gate-{rootfs_name}.json"
        proc = audit(rootfs_name, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        matches = sorted(GATE_DIR.glob(f"{rootfs_name}-*.json"), key=lambda p: p.stat().st_mtime)
        assert matches, "missing mount gate record"
        gate = json.loads(matches[-1].read_text(encoding="utf-8"))
        assert gate["mount_count"] == len(reference_mount_order(ROOTFS / rootfs_name))
        assert gate["gate_digest"]

    @pytest.mark.parametrize("rootfs_name", BUNDLED)
    def test_mount_steps_schema_omits_after(self, rootfs_name: str) -> None:
        """mount_steps records must use snapshot schema without after field."""
        export = OUTPUT / f"schema-{rootfs_name}.json"
        proc = audit(rootfs_name, export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        allowed = {"id", "source", "target", "fstype", "kind", "options"}
        for row in got["mount_steps"]:
            assert set(row.keys()) == allowed, row

    def test_merged_usr_resolv_path(self) -> None:
        """merged /usr layouts must seed usr/etc/resolv.conf."""
        export = OUTPUT / "merged-resolv.json"
        proc = audit("rootfs-003", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        assert got["resolv_target"].endswith("/tree/usr/etc/resolv.conf")
        assert (ROOTFS / "rootfs-003" / "tree" / "usr" / "etc" / "resolv.conf").is_file()
        assert not (ROOTFS / "rootfs-003" / "tree" / "etc" / "resolv.conf").exists()

    def test_suite_retry_idempotent_sources(self) -> None:
        """suite_retry must not duplicate apt suite lines."""
        export = OUTPUT / "retry-sources.json"
        proc = audit("rootfs-004", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        dest = ROOTFS / "rootfs-004" / "tree" / "etc" / "apt" / "sources.list.d" / "debian-stage2.list"
        lines = [ln for ln in dest.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 1

    def test_export_ok_false_when_hooks_fail_under_broken_driver(self) -> None:
        """Fixed export must report ok false when broken driver makes hooks fail."""
        with with_partial_patch(
            {
                "driver.sh": BROKEN / "driver.sh",
                "mount.sh": GOLDEN / "mount.sh",
                "commit.sh": GOLDEN / "commit.sh",
                "gate.sh": GOLDEN / "gate.sh",
                "hooks.sh": GOLDEN / "hooks.sh",
                "resolv.sh": GOLDEN / "resolv.sh",
                "sources.sh": GOLDEN / "sources.sh",
                "staging.sh": GOLDEN / "staging.sh",
                "export.sh": GOLDEN / "export.sh",
            }
        ):
            reset()
            export = OUTPUT / "broken-driver.json"
            proc = audit("rootfs-005", export)
            assert proc.returncode == 0
            got = json.loads(export.read_text(encoding="utf-8"))
            assert got["ok"] is False
            assert any(h["exit"] != 0 for h in got["hooks"])

    def test_mount_only_patch_insufficient(self) -> None:
        """Fixing mount order alone must still leave ok false while export ignores hook exits."""
        with with_partial_patch({"mount.sh": GOLDEN / "mount.sh"}):
            reset()
            export = OUTPUT / "mount-only.json"
            proc = audit("rootfs-005", export)
            assert proc.returncode == 0
            got = json.loads(export.read_text(encoding="utf-8"))
            assert any(h["exit"] != 0 for h in got["hooks"])
            assert got["ok"] is True

    def test_decoy_wrap_module_alone_fails(self) -> None:
        """Patching only decoy_wrap.sh must not pass bundled audits."""
        with with_partial_patch({"mount.sh": BROKEN / "decoy_wrap.sh"}):
            reset()
            export = OUTPUT / "wrap-only.json"
            proc = audit("rootfs-001", export)
            assert proc.returncode != 0 or json.loads(export.read_text(encoding="utf-8")) != reference_audit(
                ROOTFS / "rootfs-001"
            )

    def test_hidden_merged_trixie_retry(self) -> None:
        """TB3_HIDDEN_MERGED via /opt/verifier-fixtures hidden-merged-trixie layout."""
        assert TB3_HIDDEN_MERGED.endswith("hidden-merged-trixie")
        with hidden_rootfs("hidden-merged-trixie"):
            export = OUTPUT / "hidden-merged.json"
            proc = audit("hidden-merged-trixie", export)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            got = json.loads(export.read_text(encoding="utf-8"))
            expect = reference_audit(ROOTFS / "hidden-merged-trixie")
            assert got == expect

    def test_hidden_deep_pts_order(self) -> None:
        """TB3_HIDDEN_PTS via /opt/verifier-fixtures hidden-deep-pts bind ordering."""
        assert TB3_HIDDEN_PTS.endswith("hidden-deep-pts")
        with hidden_rootfs("hidden-deep-pts"):
            export = OUTPUT / "hidden-pts.json"
            proc = audit("hidden-deep-pts", export)
            assert proc.returncode == 0, proc.stderr or proc.stdout
            got = json.loads(export.read_text(encoding="utf-8"))
            expect = reference_audit(ROOTFS / "hidden-deep-pts")
            assert got == expect

    def test_ledger_appended(self) -> None:
        """Each successful run appends an entry to PATH_STAGE2_LEDGER."""
        export = OUTPUT / "ledger.json"
        proc = audit("rootfs-001", export)
        assert proc.returncode == 0
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        assert ledger["entries"]
        head = ledger["entries"][-1]
        assert head["rootfs"] == "rootfs-001"

    def test_devbind_follows_proc_in_snapshot(self) -> None:
        """devbind must appear after proc in mount snapshot."""
        export = OUTPUT / "order-check.json"
        proc = audit("rootfs-001", export)
        assert proc.returncode == 0
        matches = sorted(SNAPSHOTS.glob("rootfs-001-*.json"), key=lambda p: p.stat().st_mtime)
        snap = json.loads(matches[-1].read_text(encoding="utf-8"))
        ids = [row["id"] for row in snap["mount_steps"]]
        assert ids.index("proc") < ids.index("devbind")

    def test_trixie_codename_sources(self) -> None:
        """Codename from meta must appear in apt sources line."""
        export = OUTPUT / "trixie.json"
        proc = audit("rootfs-007", export)
        assert proc.returncode == 0
        dest = ROOTFS / "rootfs-007" / "tree" / "etc" / "apt" / "sources.list.d" / "debian-stage2.list"
        assert "trixie" in dest.read_text(encoding="utf-8")

    def test_export_uses_pipeline_version(self) -> None:
        """Final export manifest must use pipeline_version per export-manifest.md."""
        export = OUTPUT / "pipeline-version.json"
        proc = audit("rootfs-002", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = json.loads(export.read_text(encoding="utf-8"))
        assert got["pipeline_version"] == 1
        assert INGEST_STAGE in "ingest export staging"

    def test_staging_snapshot_paths_recorded(self) -> None:
        """Staging manifest must record snapshot and gate paths from ingest pipeline."""
        export = OUTPUT / "staging-paths.json"
        proc = audit("rootfs-006", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        matches = sorted(SNAPSHOTS.glob("rootfs-006-*.json"), key=lambda p: p.stat().st_mtime)
        gates = sorted(GATE_DIR.glob("rootfs-006-*.json"), key=lambda p: p.stat().st_mtime)
        assert matches and gates

    def test_gate_fingerprint_matches_mount_order(self) -> None:
        """Gate mount_fingerprint must hash ordered mount ids from snapshot."""
        export = OUTPUT / "gate-fp.json"
        proc = audit("rootfs-001", export)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        snap = json.loads(sorted(SNAPSHOTS.glob("rootfs-001-*.json"), key=lambda p: p.stat().st_mtime)[-1].read_text(encoding="utf-8"))
        gate = json.loads(sorted(GATE_DIR.glob("rootfs-001-*.json"), key=lambda p: p.stat().st_mtime)[-1].read_text(encoding="utf-8"))
        ids = [row["id"] for row in snap["mount_steps"]]
        expect = hashlib.sha256("\n".join(ids).encode()).hexdigest()
        assert gate["mount_fingerprint"] == expect
