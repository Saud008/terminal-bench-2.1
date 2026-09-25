"""Verifier: Ansible-style variable precedence resolve and sealed JSON export."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from reference_resolve import (
    copy_inventory_with_host_var,
    load_cli_export,
    reference_resolve,
    run_cli_resolve,
    seeded_var_name,
    seeded_var_value,
)

APP = Path("/app")
CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text(encoding="utf-8"))
PLAYBOOK = Path(CATALOG["playbook"])
INVENTORY = Path(CATALOG["inventory_root"])
EXTRA = Path(CATALOG["extra_vars"])
TB3_INVENTORY = Path("/opt/verifier-fixtures/inventory-tb3")
TB3_EXTRA = Path("/opt/verifier-fixtures/extra-tb3-hotfix.yml")
LIB = APP / "lib"
TESTS = Path(__file__).resolve().parent
GOLDEN_LIB = TESTS / "golden_lib"
BROKEN_LIB = TESTS / "broken_lib"


def snapshot_lib() -> dict[str, str]:
    return {str(p): p.read_text(encoding="utf-8") for p in sorted(LIB.glob("*.sh"))}


def restore_lib_snapshot(saved: dict[str, str]) -> None:
    for path, content in saved.items():
        Path(path).write_text(content, encoding="utf-8")


def install_lib_module(src: Path, dest: Path) -> None:
    data = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    dest.write_bytes(data)


def restore_broken_lib() -> None:
    for src in BROKEN_LIB.glob("*.sh"):
        install_lib_module(src, LIB / src.name)


@pytest.fixture(autouse=True)
def reset_touch() -> None:
    touch = APP / "output" / ".resolve-touch"
    touch.parent.mkdir(parents=True, exist_ok=True)
    touch.write_text("", encoding="utf-8")


@pytest.fixture(autouse=True)
def _restore_lib_after_partial() -> None:
    saved = snapshot_lib()
    yield
    restore_lib_snapshot(saved)


class TestFullStackResolve:
    @pytest.mark.parametrize("host", CATALOG["hosts"])
    @pytest.mark.parametrize("seed", CATALOG["seeds"])
    def test_full_stack_matches_reference(self, host: str, seed: str, tmp_path: Path) -> None:
        """Full resolve with extra vars matches independent reference."""
        assert callable(subprocess.run)
        out = tmp_path / f"full-{host}-{seed}.json"
        assert run_cli_resolve(PLAYBOOK, INVENTORY, host, seed, out, EXTRA) == 0
        got = load_cli_export(out)
        expect = reference_resolve(PLAYBOOK, INVENTORY, host, seed, EXTRA)
        assert got == expect

    def test_host_vars_beat_group_vars(self, tmp_path: Path) -> None:
        """Host-specific global_port must override group_vars/web.yml."""
        out = tmp_path / "host-beat.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, EXTRA)
        merged = load_cli_export(out)["merged"]
        assert merged["global_port"] == 8081
        assert merged["worker_pool"] == 8

    def test_group_files_apply_before_host(self, tmp_path: Path) -> None:
        """Group layering still contributes keys not overridden by host_vars."""
        out = tmp_path / "group-layer.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, EXTRA)
        merged = load_cli_export(out)["merged"]
        assert merged["app_label"] == "web-tier"
        assert merged["site_label"] == "corp"

    def test_role_vars_beat_defaults(self, tmp_path: Path) -> None:
        """nginx role vars override defaults for worker_connections and ssl_enabled."""
        out = tmp_path / "role-vars.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, EXTRA)
        merged = load_cli_export(out)["merged"]
        assert merged["worker_connections"] == 4096
        assert merged["ssl_enabled"] is True

    def test_defaults_fill_unset_keys(self, tmp_path: Path) -> None:
        """Role defaults still supply keys not present in role vars."""
        out = tmp_path / "defaults-fill.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, EXTRA)
        merged = load_cli_export(out)["merged"]
        assert merged["keepalive_timeout"] == 65
        assert merged["upstream_mode"] == "active"

    def test_hash_merge_preserves_nested_keys(self, tmp_path: Path) -> None:
        """hash_behaviour merge keeps sibling dict keys when overlay updates one field."""
        out = tmp_path / "hash-merge.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, EXTRA)
        cache = load_cli_export(out)["merged"]["cache"]
        assert cache["enabled"] is True
        assert cache["ttl"] == 10
        assert cache["backend"] == "mem"

    def test_include_vars_depth_order(self, tmp_path: Path) -> None:
        """Deepest include_vars entry wins include_marker and rollout_pct."""
        out = tmp_path / "include-depth.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, EXTRA)
        merged = load_cli_export(out)["merged"]
        assert merged["include_marker"] == "overlay"
        assert merged["feature_gate"]["rollout_pct"] == 90
        assert merged["feature_gate"]["channel"] == "playbook"

    def test_extra_vars_beat_playbook_vars(self, tmp_path: Path) -> None:
        """Extra vars file must override playbook vars for deploy_mode."""
        out = tmp_path / "extra-win.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, EXTRA)
        merged = load_cli_export(out)["merged"]
        assert merged["deploy_mode"] == "hotfix"
        assert merged["extra_marker"] == "rush"

    def test_inventory_beats_role_defaults_on_worker_pool(self, tmp_path: Path) -> None:
        """Host inventory must override nginx role default worker_pool on the same key."""
        out = tmp_path / "default-inv-collision.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, EXTRA)
        merged = load_cli_export(out)["merged"]
        assert merged["worker_pool"] == 8

    def test_group_vars_beat_role_defaults_without_host_override(self, tmp_path: Path) -> None:
        """Group vars override role defaults when host_vars omit the colliding key."""
        out = tmp_path / "group-over-default.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web02", "alpha01", out, EXTRA)
        merged = load_cli_export(out)["merged"]
        assert merged["worker_pool"] == 4

    def test_role_defaults_seed_value_before_inventory(self, tmp_path: Path) -> None:
        """Role defaults apply before inventory so inventory can override on collision."""
        out = tmp_path / "default-seed.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "edge01", "alpha01", out, EXTRA)
        merged = load_cli_export(out)["merged"]
        assert merged["worker_pool"] == 2

    def test_seed_injected_inventory_full_stack(self, tmp_path: Path) -> None:
        """Seed-unique injected host var survives full precedence stack."""
        seed = "delta42"
        inv = copy_inventory_with_host_var(tmp_path, seed)
        key = seeded_var_name(seed)
        out = tmp_path / "seed-full.json"
        run_cli_resolve(PLAYBOOK, inv, "web01", seed, out, EXTRA)
        got = load_cli_export(out)
        expect = reference_resolve(PLAYBOOK, inv, "web01", seed, EXTRA)
        assert got["merged"][key] == seeded_var_value(seed)
        assert got == expect

    def test_tb3_hidden_inventory_worker_pool_trap(self, tmp_path: Path) -> None:
        """TB3 host_vars in /opt/verifier-fixtures override bundled worker_pool expectations."""
        out = tmp_path / "tb3-worker-pool.json"
        run_cli_resolve(PLAYBOOK, TB3_INVENTORY, "web01", "alpha01", out, EXTRA)
        merged = load_cli_export(out)["merged"]
        expect = reference_resolve(PLAYBOOK, TB3_INVENTORY, "web01", "alpha01", EXTRA)
        assert merged["worker_pool"] == 16
        assert merged["worker_pool"] == expect["merged"]["worker_pool"]

    def test_tb3_hidden_extra_vars_deploy_mode_trap(self, tmp_path: Path) -> None:
        """TB3 extra-vars file in /opt/verifier-fixtures must beat playbook deploy_mode."""
        out = tmp_path / "tb3-extra.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, TB3_EXTRA)
        merged = load_cli_export(out)["merged"]
        expect = reference_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", TB3_EXTRA)
        assert merged["deploy_mode"] == "tb3-canary"
        assert merged["extra_marker"] == "tb3-trap"
        assert merged == expect["merged"]


class TestPartialFixTraps:
    def test_partial_ascending_sort_only_still_fails_host_override(self, tmp_path: Path) -> None:
        """Fixing group sort direction alone cannot restore host_vars precedence."""
        restore_broken_lib()
        install_lib_module(TESTS / "partial_broken_ascending_sort.sh", LIB / "inventory.sh")
        out = tmp_path / "partial-sort.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, EXTRA)
        got = load_cli_export(out)
        expect = reference_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", EXTRA)
        assert got["merged"]["global_port"] != 8081
        assert got != expect

    def test_partial_reversed_apply_loops_still_fails_reference(self, tmp_path: Path) -> None:
        """Ascending group order alone cannot fix host-before-group apply loops."""
        restore_broken_lib()
        install_lib_module(TESTS / "partial_golden_reversed_loops.sh", LIB / "inventory.sh")
        out = tmp_path / "partial-loops.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, EXTRA)
        got = load_cli_export(out)
        expect = reference_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", EXTRA)
        assert got != expect

    def test_partial_golden_role_only_still_fails_reference(self, tmp_path: Path) -> None:
        """Role defaults/vars ordering alone cannot fix broken inventory layering."""
        restore_broken_lib()
        install_lib_module(GOLDEN_LIB / "role.sh", LIB / "role.sh")
        out = tmp_path / "partial-role.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, EXTRA)
        got = load_cli_export(out)
        expect = reference_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", EXTRA)
        assert got != expect

    def test_partial_golden_inventory_only_still_fails_role_keys(self, tmp_path: Path) -> None:
        """Inventory layering alone cannot satisfy role defaults/vars precedence."""
        restore_broken_lib()
        install_lib_module(GOLDEN_LIB / "inventory.sh", LIB / "inventory.sh")
        out = tmp_path / "partial-inv.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, EXTRA)
        merged = load_cli_export(out)["merged"]
        assert merged["worker_connections"] != 4096
        assert merged["ssl_enabled"] is not True

    def test_partial_golden_merge_only_still_fails_cache(self, tmp_path: Path) -> None:
        """Recursive hash merge alone cannot preserve cache.enabled without inventory+role fixes."""
        restore_broken_lib()
        install_lib_module(GOLDEN_LIB / "merge.sh", LIB / "merge.sh")
        out = tmp_path / "partial-merge.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, EXTRA)
        got = load_cli_export(out)
        expect = reference_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", EXTRA)
        assert got != expect

    def test_partial_golden_include_only_still_fails_depth(self, tmp_path: Path) -> None:
        """Lexical include ordering alone cannot satisfy depth contract."""
        restore_broken_lib()
        install_lib_module(GOLDEN_LIB / "inventory.sh", LIB / "inventory.sh")
        install_lib_module(GOLDEN_LIB / "role.sh", LIB / "role.sh")
        install_lib_module(GOLDEN_LIB / "merge.sh", LIB / "merge.sh")
        install_lib_module(BROKEN_LIB / "include_vars.sh", LIB / "include_vars.sh")
        install_lib_module(GOLDEN_LIB / "precedence.sh", LIB / "precedence.sh")
        out = tmp_path / "partial-include.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, EXTRA)
        merged = load_cli_export(out)["merged"]
        assert merged["include_marker"] != "overlay"

    def test_partial_golden_precedence_without_extra_order_fails(self, tmp_path: Path) -> None:
        """Playbook vars still win if extra vars are merged too early."""
        restore_broken_lib()
        install_lib_module(GOLDEN_LIB / "inventory.sh", LIB / "inventory.sh")
        install_lib_module(GOLDEN_LIB / "role.sh", LIB / "role.sh")
        install_lib_module(GOLDEN_LIB / "merge.sh", LIB / "merge.sh")
        install_lib_module(GOLDEN_LIB / "include_vars.sh", LIB / "include_vars.sh")
        install_lib_module(BROKEN_LIB / "precedence.sh", LIB / "precedence.sh")
        out = tmp_path / "partial-extra.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, EXTRA)
        merged = load_cli_export(out)["merged"]
        assert merged["deploy_mode"] == "playbook-rolling"

    def test_partial_broken_precedence_inventory_before_defaults_fails(self, tmp_path: Path) -> None:
        """Merging inventory before role defaults lets defaults clobber inventory worker_pool."""
        restore_broken_lib()
        install_lib_module(GOLDEN_LIB / "inventory.sh", LIB / "inventory.sh")
        install_lib_module(GOLDEN_LIB / "role.sh", LIB / "role.sh")
        install_lib_module(GOLDEN_LIB / "merge.sh", LIB / "merge.sh")
        install_lib_module(GOLDEN_LIB / "include_vars.sh", LIB / "include_vars.sh")
        install_lib_module(BROKEN_LIB / "precedence.sh", LIB / "precedence.sh")
        out = tmp_path / "partial-precedence-order.json"
        run_cli_resolve(PLAYBOOK, INVENTORY, "web01", "alpha01", out, EXTRA)
        merged = load_cli_export(out)["merged"]
        assert merged["worker_pool"] != 8
