"""Variable precedence and inventory merge tests."""

from __future__ import annotations

import json

from conftest import load_host_rows, load_staged_snapshot, scan_cli, tree_manifest


def scan_snapshot(tree_id: str) -> dict:
    proc = scan_cli(tree_id)
    assert proc.returncode == 0, proc.stderr
    return load_staged_snapshot()


def test_precedence_trap_child_group_wins() -> None:
    """Staged host rows honor child-group precedence for precedence-trap."""
    staging = scan_snapshot("precedence-trap")
    row = next(r for r in staging["hosts"] if r["host"] == "app01")
    assert row["effective_vars"]["app_tier"] == "backend"


def test_inheritance_gap_child_group_wins() -> None:
    """Staged host rows preserve child inheritance ordering for inheritance-gap."""
    staging = scan_snapshot("inheritance-gap")
    row = next(r for r in staging["hosts"] if r["host"] == "app02")
    assert row["effective_vars"]["cluster_role"] == "compute"


def test_host_vars_override_group_vars() -> None:
    """Staged effective_vars keep host_vars above group_vars for vault-leak."""
    staging = scan_snapshot("vault-leak")
    row = next(r for r in staging["hosts"] if r["host"] == "web01")
    assert row["effective_vars"]["db_password"] == "supersecret123"


def test_vault_leak_finds_vault_exposure_category() -> None:
    """Staged exposure rows include vault_exposure findings when precedence leaks a secret."""
    staging = scan_snapshot("vault-leak")
    cats = {f["category"] for f in staging["findings"]}
    assert "vault_exposure" in cats


def test_precedence_trap_finds_precedence_shadow() -> None:
    """Staged exposure rows include precedence_shadow findings for conflicting group layers."""
    staging = scan_snapshot("precedence-trap")
    assert any(f["category"] == "precedence_shadow" for f in staging["findings"])


def test_ignored_leak_finds_ignored_file_leak() -> None:
    """Ignored inventory files still produce ignored_file_leak findings in staged rows."""
    staging = scan_snapshot("ignored-leak")
    assert any(f["category"] == "ignored_file_leak" for f in staging["findings"])


def test_ignored_vars_not_in_effective_mapping() -> None:
    """Ignored files do not leak keys into /app/state/host-rows.ndjson effective_vars."""
    staging = scan_snapshot("ignored-leak")
    row = next(r for r in staging["hosts"] if r["host"] == "edge01")
    assert "api_token" not in row["effective_vars"]


def test_merge_order_matches_hosts_ini_section_order() -> None:
    """scan-manifest merge_order mirrors the hosts.ini section sequence."""
    staging = scan_snapshot("inheritance-gap")
    assert staging["merge_order"] == ["web:hosts", "web:children", "app:hosts"]


def test_children_groups_expand_for_lineage() -> None:
    """Staged host group lineage expands parent and child groups for export."""
    staging = scan_snapshot("precedence-trap")
    row = next(r for r in staging["hosts"] if r["host"] == "app01")
    assert "web" in row["groups"] and "app" in row["groups"]


def test_group_order_parent_before_child() -> None:
    """Parent groups appear before child groups in staged host lineage."""
    staging = scan_snapshot("precedence-trap")
    row = next(r for r in staging["hosts"] if r["host"] == "app01")
    groups = row["groups"]
    assert groups.index("web") < groups.index("app")


def test_clean_tree_has_zero_findings() -> None:
    """A clean bundled tree leaves /app/state/atlas-rows.ndjson empty."""
    staging = scan_snapshot("clean-tree")
    assert staging["finding_count"] == 0


def test_expected_effective_fixture_matches_staged_rows() -> None:
    """Bundled expected-effective fixtures match the CLI-generated staged host rows."""
    staging = scan_snapshot("precedence-trap")
    expected = json.loads(
        (tree_manifest("precedence-trap").parent / "effective-contract.json").read_text(
            encoding="utf-8"
        )
    )
    row = next(r for r in staging["hosts"] if r["host"] == "app01")
    for key, value in expected["app01"].items():
        assert row["effective_vars"][key] == value


def test_scan_cli_precedence_trap_host_rows() -> None:
    """scan_cli populates /app/state/host-rows.ndjson with precedence-trap effective vars."""
    scan_cli("precedence-trap")
    rows = load_host_rows()
    app01 = next(r for r in rows if r["host"] == "app01")
    assert app01["effective_vars"]["app_tier"] == "backend"
