"""Behavioral verifier for zonefrag BIND zone include merge CLI."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference_zonefrag_bind_merge import (  # noqa: E402
    build_snapshot,
    canonical_snapshot_digest,
    merge_staging,
    publish_export,
    reference_compile,
    verify_snapshot,
)

APP = Path("/app")
CLI = Path("/usr/local/bin/zonefrag")
BUNDLES = APP / "fixtures" / "bundles"
OUTPUT = APP / "output"
STATE = Path("/app/state")
STATE_SNAPSHOT_PATH = "/app/state/foo.json"
STATE_STAGING_PATH = "/app/state/foo.json.merge-staging.json"
STATE_ZONE_CACHE_PATH = "/app/state/.zone-cache"
RESET = APP / "scripts" / "reset-state.sh"
SEEDS = json.loads((APP / "fixtures" / "seeds.json").read_text(encoding="utf-8"))["seeds"]
CATALOG = json.loads((APP / "fixtures" / "catalog.json").read_text(encoding="utf-8"))["bundles"]
HIDDEN_ROOT = Path(os.environ.get("ZONEFRAG_BUNDLE_ROOT", "/opt/verifier-fixtures"))
GOLDEN = Path(os.environ.get("ZONEFRAG_VERIFIER_GOLDEN", "/opt/verifier-golden"))
DIGESTS_PATH = APP / "fixtures" / "bundle-digests.json"
BUNDLE_DIGESTS = json.loads(DIGESTS_PATH.read_text(encoding="utf-8")) if DIGESTS_PATH.is_file() else {}
LIB = APP / "lib"
LIB_BROKEN = APP / "lib-broken"

PATCH_TARGETS = {
    "include": LIB / "include.sh",
    "wildcard": LIB / "wildcard.sh",
    "serial": LIB / "serial.sh",
    "nsec": LIB / "nsec.sh",
    "cache": LIB / "cache.sh",
    "merge": LIB / "merge.sh",
    "staging": LIB / "staging.sh",
    "export": LIB / "export.sh",
}

SUCCESS_TREES = [b["name"] for b in CATALOG]


def _tree_digest_key(tree: Path) -> str | None:
    try:
        if tree.is_relative_to(BUNDLES):
            return f"bundles/{tree.name}"
    except ValueError:
        pass
    try:
        if tree.is_relative_to(HIDDEN_ROOT):
            return f"hidden/{tree.name}"
    except ValueError:
        pass
    return None


def verify_tree_integrity(tree: Path) -> None:
    """Fail when a solution mutates bundle zone inputs after CLI execution."""
    key = _tree_digest_key(tree)
    assert key is not None, f"unknown bundle tree {tree}"
    expected = BUNDLE_DIGESTS.get(key)
    assert expected is not None, f"missing digest manifest entry for {key}"
    for rel, want in expected.items():
        path = tree / rel
        assert path.is_file(), f"missing bundle file {path} (tamper or delete)"
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        assert got == want, f"bundle input tampered: {path}"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def compile_tree(tree: Path, seed: str, out: Path, reload: bool = False) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(CLI), "compile", "--tree", str(tree), "--seed", seed, "--output", str(out)]
    if reload:
        cmd.append("--reload")
    proc = run(cmd)
    verify_tree_integrity(tree)
    return proc


def ingest_tree(tree: Path, seed: str, snap: Path, reload: bool = False) -> subprocess.CompletedProcess[str]:
    snap.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(CLI), "ingest", "--tree", str(tree), "--seed", seed, "--snapshot", str(snap)]
    if reload:
        cmd.append("--reload")
    proc = run(cmd)
    verify_tree_integrity(tree)
    return proc


def export_snap(snap: Path, out: Path) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    return run([str(CLI), "export", "--snapshot", str(snap), "--output", str(out)])


def verify_snap(snap: Path) -> tuple[int, dict]:
    proc = run([str(CLI), "verify", "--snapshot", str(snap)])
    body = json.loads((proc.stdout or "{}").strip() or "{}")
    return proc.returncode, body


def record_map(doc: dict) -> dict[tuple[str, str, str], str]:
    out: dict[tuple[str, str, str], str] = {}
    for rec in doc.get("records", []):
        out[(rec["owner"], rec["class"], rec["type"])] = rec["rdata"]
    return out


def _snapshot_sources() -> dict[str, str]:
    return {name: path.read_text(encoding="utf-8") for name, path in PATCH_TARGETS.items()}


def _restore_sources(saved: dict[str, str]) -> None:
    for name, content in saved.items():
        PATCH_TARGETS[name].write_text(content, encoding="utf-8")


def _install_golden(name: str) -> None:
    shutil.copyfile(GOLDEN / f"golden_{name}.sh", PATCH_TARGETS[name])


def _restore_broken_lib() -> None:
    assert LIB_BROKEN.is_dir(), "missing /app/lib-broken backup in image"
    for path in LIB_BROKEN.glob("*.sh"):
        shutil.copyfile(path, LIB / path.name)


@contextmanager
def _patched_from_broken(*names: str):
    saved = _snapshot_sources()
    try:
        _restore_broken_lib()
        for name in names:
            _install_golden(name)
        yield
    finally:
        _restore_sources(saved)


@pytest.fixture(autouse=True)
def _reset_output() -> None:
    reset()


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("tree_name", SUCCESS_TREES)
def test_bind9_zf_catalog_compile_matches_reference(tree_name: str, seed: str) -> None:
    """Every catalog bundle compile output must match the independent reference."""
    tree = BUNDLES / tree_name
    expected = reference_compile(tree, seed)
    out = OUTPUT / f"{tree_name}-{seed}.json"
    proc = compile_tree(tree, seed, out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads(out.read_text(encoding="utf-8"))
    assert got == expected


def test_bind9_zf_layered_precedence_www_override() -> None:
    """Later include fragment must override www A from earlier master record."""
    tree = BUNDLES / "layered-precedence"
    got = reference_compile(tree, SEEDS[0])
    rmap = record_map(got)
    assert rmap[("www", "IN", "A")] == "192.0.2.99"
    assert rmap[("mail", "IN", "A")] == "192.0.2.20"
    proc = compile_tree(tree, SEEDS[0], OUTPUT / "layered.json")
    assert proc.returncode == 0
    cli = json.loads((OUTPUT / "layered.json").read_text(encoding="utf-8"))
    assert record_map(cli)[("www", "IN", "A")] == "192.0.2.99"


def test_bind9_zf_include_order_master_interleaved() -> None:
    """processing_order must interleave master segments with includes per include-contract."""
    tree = BUNDLES / "include-order"
    expected = reference_compile(tree, SEEDS[0])
    order = expected["processing_order"]
    assert order.index("example.com.zone") < order.index("fragments/a.zone")
    assert order.index("fragments/a.zone") < order.index("fragments/b.zone")
    proc = compile_tree(tree, SEEDS[0], OUTPUT / "order.json")
    assert proc.returncode == 0
    cli = json.loads((OUTPUT / "order.json").read_text(encoding="utf-8"))
    assert cli["processing_order"] == order


def test_bind9_zf_wildcard_cross_detects_apex_overlap() -> None:
    """Merged wildcard and apex A records must surface wildcard_conflicts."""
    tree = BUNDLES / "wildcard-cross"
    expected = reference_compile(tree, SEEDS[0])
    assert len(expected["wildcard_conflicts"]) >= 1
    proc = compile_tree(tree, SEEDS[0], OUTPUT / "wild.json")
    assert proc.returncode == 0
    cli = json.loads((OUTPUT / "wild.json").read_text(encoding="utf-8"))
    assert cli["wildcard_conflicts"] == expected["wildcard_conflicts"]


def test_bind9_zf_soa_reload_uses_master_serial() -> None:
    """Reload bump must increment master SOA serial, ignoring fragment decoy SOA."""
    tree = BUNDLES / "soa-reload"
    expected = reference_compile(tree, SEEDS[0], reload=True)
    assert expected["soa_serial"] == 2026052106
    proc = compile_tree(tree, SEEDS[0], OUTPUT / "reload.json", reload=True)
    assert proc.returncode == 0
    cli = json.loads((OUTPUT / "reload.json").read_text(encoding="utf-8"))
    assert cli["soa_serial"] == 2026052106


def test_bind9_zf_nsec_chain_valid_across_includes() -> None:
    """NSEC chain must remain valid across include boundaries."""
    tree = BUNDLES / "nsec-chain"
    expected = reference_compile(tree, SEEDS[0])
    assert expected["nsec_valid"] is True
    proc = compile_tree(tree, SEEDS[0], OUTPUT / "nsec.json")
    assert proc.returncode == 0
    cli = json.loads((OUTPUT / "nsec.json").read_text(encoding="utf-8"))
    assert cli["nsec_valid"] is True


def test_bind9_zf_ingest_writes_merge_staging_artifact() -> None:
    """Ingest must write /app/state/foo.json.merge-staging.json sibling with canonical snapshot digest."""
    tree = BUNDLES / "layered-precedence"
    snap = Path(STATE_SNAPSHOT_PATH)
    proc = ingest_tree(tree, SEEDS[0], snap)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    staging_path = Path(STATE_STAGING_PATH)
    assert staging_path.is_file()
    snap_doc = json.loads(snap.read_text(encoding="utf-8"))
    staging = json.loads(staging_path.read_text(encoding="utf-8"))
    ref_staging = merge_staging(snap_doc)
    assert staging["snapshot_digest"] == ref_staging["snapshot_digest"]


def test_bind9_zf_export_reads_snapshot_only() -> None:
    """Export output must match reference export from the same ingest snapshot."""
    tree = BUNDLES / "include-order"
    snap = STATE / "pipeline-snap.json"
    out = OUTPUT / "pipeline-export.json"
    proc_ingest = ingest_tree(tree, SEEDS[1], snap)
    assert proc_ingest.returncode == 0
    proc_export = export_snap(snap, out)
    assert proc_export.returncode == 0
    snap_doc = json.loads(snap.read_text(encoding="utf-8"))
    expected = publish_export(snap_doc)
    got = json.loads(out.read_text(encoding="utf-8"))
    assert got == expected


def test_bind9_zf_verify_ok_on_clean_zone() -> None:
    """verify must report ok on bundles without wildcard or nsec issues."""
    tree = BUNDLES / "include-order"
    snap = STATE / "verify-ok.json"
    ingest_tree(tree, SEEDS[0], snap)
    rc, body = verify_snap(snap)
    assert rc == 0
    assert body.get("ok") is True


def test_bind9_zf_compile_digest_uses_canonical_snapshot() -> None:
    """compile_digest must equal canonical_snapshot_digest, not legacy key lists."""
    tree = BUNDLES / "layered-precedence"
    out = OUTPUT / "digest-check.json"
    compile_tree(tree, SEEDS[0], out)
    doc = json.loads(out.read_text(encoding="utf-8"))
    snap = build_snapshot(tree, SEEDS[0])
    assert doc["compile_digest"] == canonical_snapshot_digest(snap)


def test_bind9_zf_hidden_wildcard_bundle_via_opt_fixtures() -> None:
    """Hidden wildcard bundle under /opt/verifier-fixtures must match reference."""
    tree = HIDDEN_ROOT / "hidden-wildcard-cross"
    if not tree.is_dir():
        pytest.skip("hidden fixture not installed")
    expected = reference_compile(tree, SEEDS[0])
    proc = compile_tree(tree, SEEDS[0], OUTPUT / "hidden-wild.json")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads((OUTPUT / "hidden-wild.json").read_text(encoding="utf-8"))
    assert got == expected
    assert len(got["wildcard_conflicts"]) >= 1


def test_bind9_zf_hidden_nsec_boundary_via_opt_fixtures() -> None:
    """Hidden NSEC boundary bundle must validate chain across includes."""
    tree = HIDDEN_ROOT / "hidden-nsec-boundary"
    if not tree.is_dir():
        pytest.skip("hidden fixture not installed")
    expected = reference_compile(tree, SEEDS[0])
    proc = compile_tree(tree, SEEDS[0], OUTPUT / "hidden-nsec.json")
    assert proc.returncode == 0
    got = json.loads((OUTPUT / "hidden-nsec.json").read_text(encoding="utf-8"))
    assert got["nsec_valid"] is True
    assert got == expected


def test_bind9_zf_bundle_root_env_override_hidden() -> None:
    """ZONEFRAG_BUNDLE_ROOT env override must resolve /opt/verifier-fixtures bundle paths."""
    alt = HIDDEN_ROOT / "hidden-nsec-boundary"
    if not alt.is_dir():
        pytest.skip("hidden fixture not installed")
    expected = reference_compile(alt, SEEDS[2])
    proc = compile_tree(alt, SEEDS[2], OUTPUT / "override-hidden.json")
    assert proc.returncode == 0
    assert json.loads((OUTPUT / "override-hidden.json").read_text(encoding="utf-8")) == expected


def test_bind9_zf_cache_partial_fingerprint_in_snapshot() -> None:
    """Snapshot must store include_fingerprint for cache invalidation policy."""
    tree = BUNDLES / "cache-partial"
    snap = STATE / "cache-fp.json"
    ingest_tree(tree, SEEDS[0], snap)
    doc = json.loads(snap.read_text(encoding="utf-8"))
    ref = build_snapshot(tree, SEEDS[0])
    assert doc["include_fingerprint"] == ref["include_fingerprint"]


def test_bind9_zf_compile_populates_zone_cache_directory() -> None:
    """Compile must write cache entries under /app/state/.zone-cache."""
    tree = BUNDLES / "cache-partial"
    out = OUTPUT / "cache-zone.json"
    cache_dir = Path(STATE_ZONE_CACHE_PATH)
    proc = compile_tree(tree, SEEDS[0], out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert cache_dir.is_dir(), "missing zone cache directory"
    assert any(cache_dir.iterdir()), "zone cache must contain at least one entry after compile"


def test_bind9_zf_include_only_golden_patch_still_fails_wildcard_hidden() -> None:
    """Fixing include.sh alone must not pass hidden wildcard cross bundle."""
    tree = HIDDEN_ROOT / "hidden-wildcard-cross"
    if not tree.is_dir() or not (GOLDEN / "golden_include.sh").is_file():
        pytest.skip("probe fixtures missing")
    expected = reference_compile(tree, SEEDS[0])
    out = OUTPUT / "partial-include-hidden.json"
    with _patched_from_broken("include"):
        proc = compile_tree(tree, SEEDS[0], out)
    if proc.returncode != 0:
        return
    got = json.loads(out.read_text(encoding="utf-8"))
    if got != expected:
        return
    pytest.fail("include-only patch must not fully match hidden wildcard reference")


def test_bind9_zf_export_only_golden_patch_fails_ingest_staging() -> None:
    """Fixing export.sh alone must leave staging digest incorrect on ingest."""
    tree = BUNDLES / "layered-precedence"
    snap = STATE / "export-only-snap.json"
    with _patched_from_broken("export"):
        ingest_tree(tree, SEEDS[0], snap)
    staging_path = Path(str(snap) + ".merge-staging.json")
    if not staging_path.is_file():
        return
    snap_doc = json.loads(snap.read_text(encoding="utf-8"))
    staging = json.loads(staging_path.read_text(encoding="utf-8"))
    ref = merge_staging(snap_doc)
    if staging.get("snapshot_digest") != ref["snapshot_digest"]:
        return
    pytest.fail("export-only patch must not fix staging digest")


def test_bind9_zf_decoy_order_module_not_used_by_compile() -> None:
    """lexicographic order.sh must not define compile processing_order."""
    tree = BUNDLES / "include-order"
    expected = reference_compile(tree, SEEDS[0])
    lex_proc = run(
        [
            "bash",
            "-lc",
            "source /app/lib/common.sh; source /app/lib/order.sh; "
            f"lexicographic_include_order {tree}",
        ]
    )
    assert lex_proc.returncode == 0
    lex_lines = [ln for ln in lex_proc.stdout.splitlines() if ln.strip()]
    assert expected["processing_order"] != lex_lines


def test_bind9_zf_anti_cheat_public_fixtures_unchanged() -> None:
    """Public bundle trees must match build-time digests (no post-run tampering)."""
    assert BUNDLE_DIGESTS, "bundle-digests.json missing from image"
    for name in SUCCESS_TREES:
        verify_tree_integrity(BUNDLES / name)


def test_bind9_zf_verifier_golden_not_under_tests_tree() -> None:
    """Golden oracle patches must live outside the runtime-visible /tests tree."""
    assert GOLDEN.is_dir(), "verifier golden directory missing from image"
    assert not str(GOLDEN).startswith("/tests"), f"golden must not be under /tests: {GOLDEN}"
    assert (GOLDEN / "golden_include.sh").is_file()


def test_bind9_zf_soa_record_rdata_updated_on_reload() -> None:
    """Merged SOA rdata serial field must reflect reload bump in output records."""
    tree = BUNDLES / "soa-reload"
    out = OUTPUT / "soa-rdata.json"
    compile_tree(tree, SEEDS[0], out, reload=True)
    doc = json.loads(out.read_text(encoding="utf-8"))
    soa = next(r for r in doc["records"] if r["type"] == "SOA")
    parts = soa["rdata"].split()
    assert len(parts) >= 3
    assert parts[2] == "2026052106"


def test_bind9_zf_verify_snapshot_reference_alignment() -> None:
    """CLI verify JSON must align with reference verify_snapshot on ingest output."""
    tree = BUNDLES / "wildcard-cross"
    snap = STATE / "verify-ref.json"
    ingest_tree(tree, SEEDS[0], snap)
    snap_doc = json.loads(snap.read_text(encoding="utf-8"))
    ref = verify_snapshot(snap_doc)
    _, body = verify_snap(snap)
    assert body.get("ok") == ref["ok"]


def test_bind9_zf_api_record_present_layered_precedence() -> None:
    """Include fragment api A record must appear in merged export."""
    tree = BUNDLES / "layered-precedence"
    doc = reference_compile(tree, SEEDS[0])
    assert ("api", "IN", "A") in record_map(doc)
    proc = compile_tree(tree, SEEDS[0], OUTPUT / "api-check.json")
    assert proc.returncode == 0
    assert ("api", "IN", "A") in record_map(json.loads((OUTPUT / "api-check.json").read_text()))


def test_bind9_zf_baseline_record_include_order() -> None:
    """Master inline baseline record must survive include expansion."""
    tree = BUNDLES / "include-order"
    doc = reference_compile(tree, SEEDS[0])
    assert ("baseline", "IN", "A") in record_map(doc)


def test_bind9_zf_zone_hash_matches_reference() -> None:
    """zone_hash field must match reference canonical digest."""
    tree = BUNDLES / "nsec-chain"
    proc = compile_tree(tree, SEEDS[0], OUTPUT / "hash.json")
    assert proc.returncode == 0
    got = json.loads((OUTPUT / "hash.json").read_text(encoding="utf-8"))
    ref = reference_compile(tree, SEEDS[0])
    assert got["zone_hash"] == ref["zone_hash"]


def test_bind9_zf_double_ingest_same_seed_produces_identical_snapshot() -> None:
    """Repeated ingest with same seed must be deterministic."""
    tree = BUNDLES / "cache-partial"
    a = STATE / "double-a.json"
    b = STATE / "double-b.json"
    ingest_tree(tree, SEEDS[1], a)
    content_a = a.read_text(encoding="utf-8")
    reset()
    ingest_tree(tree, SEEDS[1], b)
    content_b = b.read_text(encoding="utf-8")
    assert json.loads(content_a) == json.loads(content_b)


def test_bind9_zf_compile_reload_false_preserves_serial() -> None:
    """Without --reload, SOA serial must remain at master value."""
    tree = BUNDLES / "soa-reload"
    doc = reference_compile(tree, SEEDS[0], reload=False)
    assert doc["soa_serial"] == 2026052105
    proc = compile_tree(tree, SEEDS[0], OUTPUT / "no-reload.json", reload=False)
    assert proc.returncode == 0
    assert json.loads((OUTPUT / "no-reload.json").read_text())["soa_serial"] == 2026052105
