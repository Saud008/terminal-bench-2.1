"""Hidden TB3 traps and partial-fix poison tests."""

from __future__ import annotations

import json

from conftest import (
    OUTPUT,
    OUTPUT_REPORT_PATH,
    STATE,
    emit_cli,
    install_partial,
    load_staged_snapshot,
    restore_lib,
    scan_cli,
    snapshot_lib,
    staging_digest_from_state_files,
    tree_manifest,
)
from vault_audit_oracle import is_vault_value


def scan_snapshot(tree_id: str) -> dict:
    proc = scan_cli(tree_id)
    assert proc.returncode == 0, proc.stderr
    return load_staged_snapshot()


def test_tb3_nested_vault_yaml_block_not_plaintext_secret() -> None:
    """Hidden tree under /opt/verifier-fixtures/tb3-trees/nested-vault."""
    manifest = tree_manifest("tb3-nested-vault")
    assert "/opt/verifier-fixtures" in str(manifest)
    staging = scan_snapshot("tb3-nested-vault")
    row = next(r for r in staging["hosts"] if r["host"] == "db01")
    val = row["effective_vars"]["db_password"]
    assert is_vault_value(val)
    assert not any(
        f["category"] == "plaintext_secret" and f["host"] == "db01"
        for f in staging["findings"]
    )


def test_tb3_nested_vault_scan_cli_passes() -> None:
    """Scan ingest against /opt/verifier-fixtures/tb3-trees/nested-vault/tree.json."""
    proc = scan_cli("tb3-nested-vault")
    assert proc.returncode == 0, proc.stderr
    meta = json.loads((STATE / "scan-manifest.json").read_text(encoding="utf-8"))
    assert meta["tree_id"] == "tb3-nested-vault"


def test_tb3_ignore_bypass_leak_finding() -> None:
    """TB3 ignore-bypass tree lives under /opt/verifier-fixtures/tb3-trees/."""
    staging = scan_snapshot("tb3-ignore-bypass")
    assert any(f["category"] == "ignored_file_leak" for f in staging["findings"])


def test_tb3_ignore_bypass_effective_vars_exclude_secret() -> None:
    staging = scan_snapshot("tb3-ignore-bypass")
    row = next(r for r in staging["hosts"] if r["host"] == "cache01")
    assert "redis_password" not in row["effective_vars"]


def test_tb3_ignore_bypass_emit_report() -> None:
    """TB3 emit still writes a report from staged rows after scan completes."""
    out = OUTPUT / "hosts-atlas-report.json"
    scan_cli("tb3-ignore-bypass")
    proc = emit_cli("tb3-ignore-bypass", out)
    assert proc.returncode == 0
    assert str(out) == OUTPUT_REPORT_PATH
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["tree_id"] == "tb3-ignore-bypass"


def test_partial_emit_reopen_trap_fails_without_fix() -> None:
    """A poisoned emit hook changes the report only if emit wrongly reopens inventory files."""
    saved = snapshot_lib()
    try:
        scan_cli("vault-leak")
        staged_digest = json.loads(
            (STATE / "scan-manifest.json").read_text(encoding="utf-8")
        )["staging_digest"]
        inv = tree_manifest("vault-leak").parent / "inventory"
        host_vars = next((inv / "host_vars").glob("*.yml"))
        original = host_vars.read_text(encoding="utf-8")
        host_vars.write_text("db_password: mutated-plain\n", encoding="utf-8")
        install_partial("emit_reopen.sh")
        out = OUTPUT / "hosts-atlas-report.json"
        proc = emit_cli("vault-leak", out)
        assert proc.returncode == 0, proc.stderr
        report = json.loads(out.read_text(encoding="utf-8"))
        assert report["staging_digest"] != staged_digest
        host_vars.write_text(original, encoding="utf-8")
    finally:
        restore_lib(saved)


def test_partial_broken_digest_trap_changes_digest() -> None:
    """A poisoned scan hook changes staging_digest only if staged bytes differ from the contract."""
    saved = snapshot_lib()
    try:
        install_partial("digest_trap.sh")
        scan_cli("vault-leak")
        meta = json.loads((STATE / "scan-manifest.json").read_text(encoding="utf-8"))
        assert meta["staging_digest"] != staging_digest_from_state_files()
    finally:
        restore_lib(saved)


def test_vault_marker_whitespace_trimmed() -> None:
    """Vault markers stay recognized after whitespace trim in staged parsing."""
    raw = "  $ANSIBLE_VAULT;1.1;AES256;deadbeef  "
    assert is_vault_value(raw)


def test_emit_wrong_tree_id_exits_3() -> None:
    """emit exits 3 when /app/state/active-tree.id does not match the requested tree."""
    scan_cli("clean-tree")
    out = OUTPUT / "hosts-atlas-report.json"
    proc = emit_cli("vault-leak", out)
    assert proc.returncode == 3


def test_scan_manifest_finding_count_matches_rows() -> None:
    """scan-manifest finding_count matches the staged /app/state/atlas-rows.ndjson row count."""
    scan_cli("ignored-leak")
    meta = json.loads((STATE / "scan-manifest.json").read_text(encoding="utf-8"))
    rows = [
    json.loads(line)
    for line in (STATE / "atlas-rows.ndjson").read_text(encoding="utf-8").splitlines()
    if line.strip()
    ]
    assert meta["finding_count"] == len(rows)
