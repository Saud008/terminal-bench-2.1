"""Scan and emit CLI contract tests (scan ingest / emit export stages)."""

from __future__ import annotations

import json

import pytest
from conftest import (
    APP,
    CLI,
    OUTPUT,
    OUTPUT_REPORT_PATH,
    STATE,
    STATE_EXPOSURE_ROWS,
    STATE_HOST_ROWS,
    STATE_RUN_SEQ,
    STATE_SCAN_MANIFEST,
    emit_cli,
    load_scan_manifest,
    load_staged_snapshot,
    run,
    scan_cli,
    staging_digest_from_state_files,
    tree_manifest,
)
from vault_audit_oracle import (
    reference_scan_snapshot as scan_oracle,
)
from vault_audit_oracle import (
    render_exposure_ledger,
    sha256_bytes,
)


def test_cli_installed_on_path() -> None:
    """CLI is installed at /usr/local/bin/hostsatlas per instruction.md."""
    assert CLI.is_file()
    assert CLI.stat().st_mode & 0o111


def test_scan_missing_manifest_exits_2() -> None:
    """scan exits 2 when the tree manifest path is absent."""
    missing = tree_manifest("clean-tree").with_name("missing.json")
    proc = run([str(CLI), "scan", "--tree", str(missing)])
    assert proc.returncode == 2


def test_emit_without_scan_exits_3() -> None:
    """emit exits 3 before /app/state/scan-manifest.json exists for the requested tree."""
    out = OUTPUT / "hosts-atlas-report.json"
    proc = emit_cli("clean-tree", out)
    assert proc.returncode == 3


def test_scan_writes_scan_manifest() -> None:
    """scan writes /app/state/scan-manifest.json with tree_id, staging_digest, and merge_order."""
    proc = scan_cli("clean-tree")
    assert proc.returncode == 0, proc.stderr
    assert STATE_SCAN_MANIFEST == "/app/state/scan-manifest.json"
    assert str(STATE / "scan-manifest.json") == STATE_SCAN_MANIFEST
    meta = load_scan_manifest()
    assert meta["tree_id"] == "clean-tree"
    assert "staging_digest" in meta
    assert "merge_order" in meta


def test_scan_writes_host_rows_ndjson() -> None:
    """scan writes /app/state/host-rows.ndjson staging rows for effective inventory state."""
    scan_cli("clean-tree")
    assert STATE_HOST_ROWS == "/app/state/host-rows.ndjson"
    assert str(STATE / "host-rows.ndjson") == STATE_HOST_ROWS
    lines = (STATE / "host-rows.ndjson").read_text(encoding="utf-8").strip().splitlines()
    assert lines
    row = json.loads(lines[0])
    assert "host" in row and "groups" in row and "effective_vars" in row


def test_scan_writes_exposure_rows_ndjson() -> None:
    """scan writes /app/state/atlas-rows.ndjson findings for bundled leak fixtures."""
    scan_cli("vault-leak")
    path = STATE / "atlas-rows.ndjson"
    assert STATE_EXPOSURE_ROWS == "/app/state/atlas-rows.ndjson"
    assert str(path) == STATE_EXPOSURE_ROWS
    assert path.is_file()
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows
    assert rows[0]["category"] in {
        "vault_exposure",
        "plaintext_secret",
        "precedence_shadow",
        "ignored_file_leak",
    }


def test_staging_digest_includes_findings_bytes() -> None:
    """staging_digest hashes the exact staged NDJSON bytes from /app/state."""
    scan_cli("vault-leak")
    meta = load_scan_manifest()
    hosts_blob = (STATE / "host-rows.ndjson").read_bytes()
    findings_blob = (STATE / "atlas-rows.ndjson").read_bytes()
    assert hosts_blob.endswith(b"\n")
    assert findings_blob.endswith(b"\n")
    assert meta["staging_digest"] == staging_digest_from_state_files()
    hosts_only = sha256_bytes(hosts_blob)
    assert meta["staging_digest"] != hosts_only
    assert findings_blob


def test_emit_produces_vault_exposure_report() -> None:
    """emit writes /app/output/hosts-atlas-report.json using staged scan artifacts."""
    out = OUTPUT / "hosts-atlas-report.json"
    scan_cli("vault-leak")
    proc = emit_cli("vault-leak", out)
    assert proc.returncode == 0, proc.stderr
    assert OUTPUT_REPORT_PATH == "/app/output/hosts-atlas-report.json"
    assert str(out) == OUTPUT_REPORT_PATH
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["schema_version"] == "1"
    assert report["tree_id"] == "vault-leak"
    assert "findings" in report and "summary" in report
    assert "group_lineage" in report and "merge_order" in report


def test_emit_findings_sorted_by_category_host_var_key() -> None:
    """Report findings are sorted as documented in /app/docs/risk-report-schema.md."""
    out = OUTPUT / "hosts-atlas-report.json"
    scan_cli("precedence-trap")
    emit_cli("precedence-trap", out)
    findings = json.loads(out.read_text(encoding="utf-8"))["findings"]
    keys = [(f["category"], f["host"], f["var_key"]) for f in findings]
    assert keys == sorted(keys)


def test_emit_reads_staging_only_not_inventory_tree() -> None:
    """emit reuses /app/state staging and does not reopen inventory hosts.ini after scan."""
    out = OUTPUT / "hosts-atlas-report.json"
    scan_cli("clean-tree")
    inv_hosts = tree_manifest("clean-tree").parent / "inventory" / "hosts.ini"
    original = inv_hosts.read_text(encoding="utf-8")
    try:
        inv_hosts.write_text(original + "\n# mutated\n", encoding="utf-8")
        proc = emit_cli("clean-tree", out)
        assert proc.returncode == 0
        report = json.loads(out.read_text(encoding="utf-8"))
        ref = render_exposure_ledger(load_staged_snapshot(), run_seq=report["run_seq"])
        assert report["staging_digest"] == ref["staging_digest"]
    finally:
        inv_hosts.write_text(original, encoding="utf-8")


def test_rescan_same_tree_keeps_run_seq() -> None:
    """Re-scanning an unchanged tree keeps /app/state/run-seq.json stable."""
    scan_cli("clean-tree")
    assert STATE_RUN_SEQ == "/app/state/run-seq.json"
    assert str(STATE / "run-seq.json") == STATE_RUN_SEQ
    seq1 = json.loads((STATE / "run-seq.json").read_text(encoding="utf-8"))["run_seq"]
    scan_cli("clean-tree")
    seq2 = json.loads((STATE / "run-seq.json").read_text(encoding="utf-8"))["run_seq"]
    assert seq1 == seq2


def test_rescan_different_tree_increments_run_seq() -> None:
    """A new tree fingerprint increments /app/state/run-seq.json."""
    scan_cli("clean-tree")
    seq1 = json.loads((STATE / "run-seq.json").read_text(encoding="utf-8"))["run_seq"]
    scan_cli("vault-leak")
    seq2 = json.loads((STATE / "run-seq.json").read_text(encoding="utf-8"))["run_seq"]
    assert seq2 == seq1 + 1


def test_rescan_same_tree_reproduces_staging_digest() -> None:
    """Unchanged scans reproduce the same staging_digest across repeated runs."""
    scan_cli("precedence-trap")
    d1 = json.loads((STATE / "scan-manifest.json").read_text(encoding="utf-8"))["staging_digest"]
    scan_cli("precedence-trap")
    d2 = json.loads((STATE / "scan-manifest.json").read_text(encoding="utf-8"))["staging_digest"]
    assert d1 == d2


@pytest.mark.parametrize("tree_id", ["clean-tree", "vault-leak", "precedence-trap", "ignored-leak"])
def test_scan_host_count_matches_oracle(tree_id: str) -> None:
    """scan-manifest host_count matches the independent bundled-tree oracle."""
    scan_cli(tree_id)
    meta = load_scan_manifest()
    ref = scan_oracle(tree_manifest(tree_id))
    assert meta["host_count"] == ref["host_count"]


@pytest.mark.parametrize("tree_id", ["clean-tree", "vault-leak", "precedence-trap", "ignored-leak", "inheritance-gap"])
def test_bundled_tree_finding_count_matches_oracle(tree_id: str) -> None:
    """scan-manifest finding_count matches the independent bundled-tree oracle."""
    scan_cli(tree_id)
    meta = load_scan_manifest()
    ref = scan_oracle(tree_manifest(tree_id))
    assert meta["finding_count"] == ref["finding_count"]


def test_decoy_vault_decrypt_not_on_cli_hot_path() -> None:
    """The decoy decrypt helper is outside the scan and emit hot paths."""
    decoy = APP / "decoy/decoy-legacy-helper.sh"
    assert decoy.is_file()
    cli_text = (APP / "scripts/hostsatlas").read_text(encoding="utf-8")
    assert "decoy-legacy-helper" not in cli_text


def test_wrap_legacy_merge_not_on_scan_hot_path() -> None:
    """The legacy merge wrapper is not called from /app/lib/scan_inventory.sh."""
    wrap = APP / "wrap/legacy-inventory-merge.sh"
    assert wrap.is_file()
    scan_sh = (APP / "lib" / "scan_inventory.sh").read_text(encoding="utf-8")
    assert "legacy-inventory-merge" not in scan_sh
