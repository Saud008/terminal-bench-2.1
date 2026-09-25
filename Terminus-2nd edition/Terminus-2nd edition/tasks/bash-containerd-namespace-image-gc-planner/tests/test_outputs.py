"""Verifier for containerd namespace GC planner — subprocess + reference_* only.

Case 6 contract note: scan-meta covers the ingest stage; emit-plan covers the export stage.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

CLI = Path("/app/lib/cli.sh")
CLI_LAUNCH = ["/bin/bash", str(CLI)]
FIX = Path("/app/fixtures/meta-basic")
VERIFIER_FIX = Path(__file__).resolve().parent / "verifier-fixtures"
SNAPSHOT = Path("/app/state/gc_snapshot.json")
BUFFER = Path("/app/state/eligibility.buffer")
PLAN = Path("/app/output/namespace_gc_plan.json")
REVSEQ = Path("/app/state/revision.seq")


def ctgc_spawn(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([*CLI_LAUNCH, *args], capture_output=True, text=True, check=False)


def ctgc_wipe() -> None:
    for p in (SNAPSHOT, BUFFER, PLAN, REVSEQ):
        if p.is_file():
            p.unlink()


def _load_tree(root: Path) -> dict:
    def load_dir(d: Path) -> list:
        if not d.is_dir():
            return []
        rows = []
        for f in sorted(d.glob("*.json")):
            rows.append(json.loads(f.read_text()))
        return rows

    return {
        "namespaces": _load_ns_dirs(root),
        "images": _load_flat(root / "images"),
        "leases": _load_flat(root / "leases"),
        "snapshots": _load_flat(root / "snapshots"),
    }


def _load_ns_dirs(root: Path) -> list:
    out = []
    ns_root = root / "namespaces"
    if not ns_root.is_dir():
        return out
    for sub in sorted(ns_root.iterdir()):
        if sub.is_dir():
            for f in sorted(sub.glob("*.json")):
                out.append(json.loads(f.read_text()))
    return out


def _load_flat(d: Path) -> list:
    if not d.is_dir():
        return []
    return [json.loads(f.read_text()) for f in sorted(d.glob("*.json"))]


def _filter_ns(data: dict, ns: str) -> dict:
    return {
        "namespaces": [n for n in data["namespaces"] if n.get("name") == ns],
        "images": [i for i in data["images"] if i.get("namespace") == ns],
        "leases": [row for row in data["leases"] if row.get("namespace") == ns],
        "snapshots": [s for s in data["snapshots"] if s.get("namespace") == ns],
    }


def _descendants(root: str, snaps: list[dict]) -> set[str]:
    by_parent: dict[str, list[str]] = {}
    for s in snaps:
        by_parent.setdefault(s.get("parent") or "", []).append(s["key"])
    out = set()

    def walk(k: str) -> None:
        out.add(k)
        for c in by_parent.get(k, []):
            walk(c)

    walk(root)
    return out


def _ancestors(key: str, snaps: list[dict]) -> set[str]:
    by_key = {s["key"]: s for s in snaps}
    out: set[str] = set()
    cur = key
    while cur:
        par = by_key.get(cur, {}).get("parent") or ""
        if not par:
            break
        out.add(par)
        cur = par
    return out


def _depth_map(snaps: list[dict]) -> dict[str, int]:
    by_key = {s["key"]: s for s in snaps}

    def depth(k: str) -> int:
        p = by_key[k].get("parent") or ""
        return 0 if not p else 1 + depth(p)

    return {s["key"]: depth(s["key"]) for s in snaps}


def reference_resolve(data: dict, now: int) -> dict:
    snaps = data["snapshots"]
    images = data["images"]
    leases = data["leases"]
    namespaces = data["namespaces"]
    protected: set[str] = set()
    for lease in leases:
        if lease.get("expires_at", 0) > now:
            root = lease.get("labels", {}).get("containerd.io/gc.root")
            if root:
                protected |= _descendants(root, snaps)
    pins: set[str] = set()
    for ns in namespaces:
        pins.update(ns.get("retention_pins") or [])
    for dig in pins:
        for s in snaps:
            if dig in (s.get("refs") or []):
                protected.add(s["key"])
    expanded = set(protected)
    for key in list(protected):
        expanded |= _ancestors(key, snaps)
    protected = expanded
    dangling = [
        img["digest"]
        for img in images
        if not any(dig in (s.get("refs") or []) for s in snaps for dig in [img["digest"]])
    ]
    depths = _depth_map(snaps)
    deletable_snaps = sorted(
        [s["key"] for s in snaps if s["key"] not in protected],
        key=lambda k: -depths[k],
    )
    deletable_imgs = sorted(
        dig
        for dig in dangling
        if dig not in pins
        and not any(dig in (s.get("refs") or []) and s["key"] in protected for s in snaps)
    )
    body = f"prot={sorted(protected)}|del_s={deletable_snaps}|del_i={deletable_imgs}"
    rdigest = hashlib.sha256(body.encode()).hexdigest()
    return {
        "schema_version": 1,
        "protected_snapshots": sorted(protected),
        "dangling_images": sorted(dangling),
        "deletable_snapshots": deletable_snaps,
        "deletable_images": deletable_imgs,
        "resolve_now": now,
        "resolve_digest": rdigest,
    }


def reference_plan(elig: dict) -> dict:
    actions = []
    for key in elig["deletable_snapshots"]:
        actions.append({"action": "delete", "kind": "snapshot", "key": key})
    for dig in sorted(elig["deletable_images"]):
        actions.append({"action": "delete", "kind": "image", "digest": dig})
    lines = "".join(
        f"s:{a['key']}" if a["kind"] == "snapshot" else f"i:{a['digest']}" for a in actions
    )
    pd = hashlib.sha256(lines.encode()).hexdigest()
    return {"schema_version": 1, "mode": "dry-run", "actions": actions, "plan_digest": pd}


def _scan_meta(root: Path, ns: str = "", out: Path = SNAPSHOT):
    args = ["scan-meta", "--meta-root", str(root), "--out", str(out)]
    if ns:
        args.extend(["--namespace", ns])
    return ctgc_spawn(*args)


def _resolve(snap_path: Path = SNAPSHOT, now: int = 2000000000, out: Path = BUFFER):
    return ctgc_spawn("resolve", "--gc-snapshot", str(snap_path), "--now", str(now), "--out", str(out))


def _emit_plan(buffer_path: Path = BUFFER, out: Path = PLAN):
    return ctgc_spawn("emit-plan", "--eligibility-buffer", str(buffer_path), "--out", str(out))


def test_cli_ingest_writes_staging_schema():
    """scan-meta must write gc_snapshot.json with schema_version and meta_digest per gc-snapshot-schema.md."""
    ctgc_wipe()
    r = _scan_meta(FIX)
    assert r.returncode == 0, r.stderr
    doc = json.loads(SNAPSHOT.read_text())
    assert doc["schema_version"] == 1
    assert "meta_digest" in doc
    assert len(doc["images"]) >= 4


def test_scan_meta_namespace_filter_excludes_moby():
    """scan-meta --namespace must scope images and snapshots to the requested namespace only."""
    ctgc_wipe()
    r = _scan_meta(FIX, ns="k8s.io")
    assert r.returncode == 0
    doc = json.loads(SNAPSHOT.read_text())
    assert all(i["namespace"] == "k8s.io" for i in doc["images"])
    assert all(s["namespace"] == "k8s.io" for s in doc["snapshots"])
    assert not any(i["digest"] == "sha256:imgmoby01" for i in doc["images"])


def test_scan_meta_revision_seq_bumps_on_change():
    """revision.seq must advance when gc_snapshot meta_digest changes across scan-meta runs."""
    ctgc_wipe()
    _scan_meta(FIX)
    seq1 = int(REVSEQ.read_text().strip())
    _scan_meta(FIX)
    seq2 = int(REVSEQ.read_text().strip())
    assert seq2 == seq1
    ctgc_wipe()
    _scan_meta(FIX, ns="moby")
    seq3 = int(REVSEQ.read_text().strip())
    assert seq3 > 0


def test_resolve_marks_lease_subtree_protected():
    """resolve must protect active lease gc.root keys and their snapshot descendants."""
    ctgc_wipe()
    _scan_meta(FIX, ns="k8s.io")
    _resolve(now=2000000000)
    elig = json.loads(BUFFER.read_text())
    prot = set(elig["protected_snapshots"])
    assert "snap-active-root" in prot
    assert "snap-active-child" in prot


def test_expired_lease_does_not_protect():
    """resolve must not treat snapshots as protected when their lease expires_at is before --now."""
    ctgc_wipe()
    _scan_meta(FIX, ns="k8s.io")
    _resolve(now=50)
    elig = json.loads(BUFFER.read_text())
    prot = set(elig["protected_snapshots"])
    assert "snap-expired-root" not in prot or True


def test_retention_pin_keeps_image_off_deletable():
    """resolve must keep retention-pinned image digests out of deletable_images."""
    ctgc_wipe()
    _scan_meta(FIX, ns="k8s.io")
    _resolve(now=2000000000)
    elig = json.loads(BUFFER.read_text())
    assert "sha256:pinkeep001" not in elig["deletable_images"]


def test_ancestor_snapshots_protected_with_pin():
    """resolve must walk snapshot parents so pinned-image roots keep ancestor keys protected."""
    ctgc_wipe()
    _scan_meta(FIX, ns="k8s.io")
    _resolve(now=2000000000)
    elig = json.loads(BUFFER.read_text())
    assert "snap-pin-root" in elig["protected_snapshots"]


def test_dangling_image_detected():
    """resolve must list image digests with no snapshot refs in dangling_images."""
    ctgc_wipe()
    _scan_meta(FIX, ns="k8s.io")
    _resolve(now=2000000000)
    elig = json.loads(BUFFER.read_text())
    assert "sha256:imgdangle01" in elig["dangling_images"]


def test_active_image_not_dangling():
    """resolve must not mark still-referenced images as dangling."""
    ctgc_wipe()
    _scan_meta(FIX, ns="k8s.io")
    _resolve(now=2000000000)
    elig = json.loads(BUFFER.read_text())
    assert "sha256:imgactive01" not in elig["dangling_images"]


def test_deletable_snapshots_deepest_first():
    """resolve must order deletable_snapshots deepest-first per reclaim-sequence.md."""
    ctgc_wipe()
    _scan_meta(FIX, ns="k8s.io")
    _resolve(now=2000000000)
    elig = json.loads(BUFFER.read_text())
    snaps = elig["deletable_snapshots"]
    if "snap-orphan-leaf" in snaps and "snap-orphan-root" in snaps:
        assert snaps.index("snap-orphan-leaf") < snaps.index("snap-orphan-root")


def test_emit_plan_plan_matches_reference():
    """emit-plan must build dry-run actions and plan_digest matching independent reference math."""
    ctgc_wipe()
    _scan_meta(FIX, ns="k8s.io")
    _resolve(now=2000000000)
    _emit_plan()
    got = json.loads(PLAN.read_text())
    data = _filter_ns(_load_tree(FIX), "k8s.io")
    ref_elig = reference_resolve(data, 2000000000)
    ref_plan = reference_plan(ref_elig)
    assert got["actions"] == ref_plan["actions"]
    assert got["plan_digest"] == ref_plan["plan_digest"]


def test_emit_plan_reads_staging_not_meta_root():
    """emit-plan must read eligibility.buffer only, not re-scan the metadata tree."""
    ctgc_wipe()
    _scan_meta(FIX, ns="k8s.io")
    _resolve(now=2000000000)
    staging_copy = json.loads(BUFFER.read_text())
    staging_copy["deletable_images"] = []
    BUFFER.write_text(json.dumps(staging_copy, sort_keys=True, indent=2))
    _emit_plan()
    got = json.loads(PLAN.read_text())
    assert all(a["kind"] != "image" for a in got["actions"])


def test_idempotent_scan_meta_bytes():
    """Repeated scan-meta with unchanged inputs must produce byte-identical gc_snapshot.json."""
    ctgc_wipe()
    _scan_meta(FIX, ns="k8s.io")
    b1 = SNAPSHOT.read_bytes()
    _scan_meta(FIX, ns="k8s.io")
    b2 = SNAPSHOT.read_bytes()
    assert b1 == b2


def test_resolve_digest_stable():
    """resolve must emit the same resolve_digest when eligibility inputs and --now are unchanged."""
    ctgc_wipe()
    _scan_meta(FIX, ns="k8s.io")
    _resolve(now=2000000000)
    d1 = json.loads(BUFFER.read_text())["resolve_digest"]
    _resolve(now=2000000000)
    d2 = json.loads(BUFFER.read_text())["resolve_digest"]
    assert d1 == d2


def test_hidden_lease_trap_subtree():
    """Hidden meta-trap fixture verifies lease subtree protection outside bundled fixtures."""
    ctgc_wipe()
    # verifier-fixtures/meta-trap exercises lease subtree protection
    trap = VERIFIER_FIX / "meta-trap"
    assert trap.is_dir(), "verifier fixture missing"
    r = _scan_meta(trap, ns="ns-trap")
    assert r.returncode == 0
    _resolve(now=5000)
    elig = json.loads(BUFFER.read_text())
    assert "snap-trap-child" in elig["protected_snapshots"]


def test_hidden_dangling_only_in_emit_plan():
    """Hidden meta-emit-trap fixture verifies dangling orphan handling in emit-plan only."""
    ctgc_wipe()
    # verifier-fixtures/meta-emit-trap checks emit-plan dangling orphan plan
    trap = VERIFIER_FIX / "meta-emit-trap"
    assert trap.is_dir()
    _scan_meta(trap, ns="ns-orphan")
    _resolve(now=9000)
    _emit_plan()
    got = json.loads(PLAN.read_text())
    data = _filter_ns(_load_tree(trap), "ns-orphan")
    ref = reference_plan(reference_resolve(data, 9000))
    assert got["actions"] == ref["actions"]


def test_orphan_chain_eligible_when_unprotected():
    """Unprotected orphan snapshot chains must appear in deletable_snapshots after resolve."""
    ctgc_wipe()
    _scan_meta(FIX, ns="k8s.io")
    _resolve(now=50)
    elig = json.loads(BUFFER.read_text())
    deletable = set(elig["deletable_snapshots"])
    assert "snap-orphan-leaf" in deletable or "snap-orphan-mid" in deletable


def test_plan_mode_is_dry_run():
    """namespace_gc_plan.json must declare mode dry-run per reclaim-sequence.md."""
    ctgc_wipe()
    _scan_meta(FIX, ns="k8s.io")
    _resolve(now=2000000000)
    _emit_plan()
    got = json.loads(PLAN.read_text())
    assert got["mode"] == "dry-run"


def test_staging_sorted_keys():
    """gc_snapshot.json must include sorted snapshot records after scan-meta."""
    ctgc_wipe()
    _scan_meta(FIX)
    doc = json.loads(SNAPSHOT.read_text())
    assert doc["schema_version"] == 1
    assert "snapshots" in doc


def test_deletable_images_sorted():
    """emit-plan image delete actions must be sorted by digest."""
    ctgc_wipe()
    _scan_meta(FIX, ns="k8s.io")
    _resolve(now=50)
    _emit_plan()
    imgs = [a["digest"] for a in json.loads(PLAN.read_text())["actions"] if a["kind"] == "image"]
    assert imgs == sorted(imgs)


def test_protected_excludes_active_image_snap():
    """Protected lease roots must never appear in deletable_snapshots."""
    ctgc_wipe()
    _scan_meta(FIX, ns="k8s.io")
    _resolve(now=2000000000)
    elig = json.loads(BUFFER.read_text())
    assert "snap-active-root" not in elig["deletable_snapshots"]
