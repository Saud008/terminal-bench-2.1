"""Behavioral verifier for iptctl simulate CLI."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

from iptctl_replay_model import (
    merge_staging_path,
    reference_export_from_staging,
    reference_simulate,
    reference_staging,
)

APP = Path("/app")
CLI = APP / "scripts" / "iptctl"
RESTORES = APP / "fixtures/restores"
OUTPUT = APP / "output"
STATE = APP / "state/work"
LIB = APP / "lib"
TESTS = Path(__file__).resolve().parent
GOLDEN = TESTS / "verifier-patch-libs"
TRAPS = TESTS / "partial-patch-traps"
RESET = APP / "scripts/reset-state.sh"
SEED_DOC = json.loads((APP / "fixtures/seeds.json").read_text(encoding="utf-8"))

DOC_MARK_VISIBILITY_LATTICE = "/app/docs/mark-visibility-lattice-contract.md"
DOC_EXAMPLE_STAGING = "/app/state/example.staging.json"
DOC_FOO_STAGING = "/app/state/foo.staging.json"
DOC_FOO_MERGE = "/app/state/foo.staging.json.merge-staging.json"

RESTORE_NAMES = SEED_DOC["restores"]
SEEDS = SEED_DOC["seeds"]

HIDDEN_RESTORES = Path("/opt/verifier-fixtures/tb3-restores")

INGEST_CORE_GOLDEN = {
    "rule_lexer.sh": GOLDEN / "patch_lib_rule_lexer.sh",
    "table_commit_order.sh": GOLDEN / "patch_lib_table_commit_order.sh",
    "chain_policy_mode.sh": GOLDEN / "patch_lib_chain_policy_mode.sh",
    "rule_counter_mode.sh": GOLDEN / "patch_lib_rule_counter_mode.sh",
    "nat_mark_bridge.sh": GOLDEN / "patch_lib_nat_mark_bridge.sh",
    "ct_order_mode.sh": GOLDEN / "patch_lib_ct_order_mode.sh",
    "plan_binding.sh": GOLDEN / "patch_lib_plan_binding.sh",
    "merge_stage_writer.sh": GOLDEN / "patch_lib_merge_stage_writer.sh",
}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def simulate(restore: Path, seed: str, out: Path) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    return run(
        [
            str(CLI),
            "simulate",
            "--restore",
            str(restore),
            "--seed",
            seed,
            "--export",
            str(out),
        ]
    )


def ingest(restore: Path, snapshot: Path) -> subprocess.CompletedProcess[str]:
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    return run(
        [
            str(CLI),
            "ingest",
            "--restore",
            str(restore),
            "--snapshot",
            str(snapshot),
        ]
    )


def export_snapshot(snapshot: Path, seed: str, out: Path) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    return run(
        [
            str(CLI),
            "export",
            "--snapshot",
            str(snapshot),
            "--seed",
            seed,
            "--export",
            str(out),
        ]
    )


def protected_hashes() -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted((APP / "fixtures").rglob("*")):
        if path.is_file():
            rel = path.relative_to(APP / "fixtures").as_posix()
            out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


PROTECTED_SHA256 = protected_hashes()


def _copy_lib_script(src: Path, dest: Path) -> None:
    """Copy a lib shell script with LF line endings (Harbor runs on Linux)."""
    text = src.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    dest.write_text(text, encoding="utf-8")


def oracle_ready() -> bool:
    reset()
    try:
        restore = RESTORES / "triple-order.v4"
        expected = reference_simulate(restore, "1")
        out = OUTPUT / "oracle-probe.json"
        proc = simulate(restore, "1", out)
        if proc.returncode != 0:
            return False
        got = json.loads(out.read_text(encoding="utf-8"))
        return got == expected
    except Exception:
        return False


@contextmanager
def with_partial_patch(modules: dict[str, Path]):
    saved = {name: (LIB / name).read_text(encoding="utf-8") for name in modules}
    try:
        for name, src in modules.items():
            _copy_lib_script(src, LIB / name)
        yield
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")
        reset()


class TestIptctlKernelReplayVerifier:
    def setup_method(self) -> None:
        reset()

    def test_iptctl_fixture_bytes_immutable(self) -> None:
        """Fixture tree must not be modified at runtime."""
        current: dict[str, str] = {}
        for path in sorted((APP / "fixtures").rglob("*")):
            if path.is_file():
                rel = path.relative_to(APP / "fixtures").as_posix()
                current[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        assert current == PROTECTED_SHA256

    @pytest.mark.parametrize("name", RESTORE_NAMES)
    @pytest.mark.parametrize("seed", SEEDS)
    def test_iptctl_report_matches_reference(self, name: str, seed: str) -> None:
        """Every catalog restore and seed must match the reference simulator."""
        restore = RESTORES / f"{name}.v4"
        expected = reference_simulate(restore, seed)
        out = OUTPUT / f"{name}-{seed}.json"
        proc = simulate(restore, seed, out)
        assert proc.returncode == expected["exit_code"], proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        assert got == expected

    def test_iptctl_missing_restore_exits_two(self) -> None:
        """Missing restore file must export exit_code 2."""
        out = OUTPUT / "missing.json"
        proc = simulate(RESTORES / "does-not-exist.v4", "1", out)
        assert proc.returncode == 2
        report = json.loads(out.read_text(encoding="utf-8"))
        assert report["exit_code"] == 2
        assert report["rules"] == []

    def test_iptctl_mangle_mark_nat_activation(self) -> None:
        """NAT mark rules must activate only after mangle marks are committed."""
        restore = RESTORES / "mangle-mark.v4"
        expected = reference_simulate(restore, "7")
        proc = simulate(restore, "7", OUTPUT / "mark-probe.json")
        assert proc.returncode == 0
        got = json.loads((OUTPUT / "mark-probe.json").read_text(encoding="utf-8"))
        assert got == expected
        nat_rules = [r for r in got["rules"] if r["table"] == "nat"]
        assert any(r["nat_active"] for r in nat_rules)
        assert not all(r["nat_active"] for r in nat_rules)

    def test_iptctl_policy_counters_preserved(self) -> None:
        """Chain policy counters from restore must survive simulation."""
        restore = RESTORES / "core-filter.v4"
        expected = reference_simulate(restore, "11")
        proc = simulate(restore, "11", OUTPUT / "policy-probe.json")
        assert proc.returncode == 0
        got = json.loads((OUTPUT / "policy-probe.json").read_text(encoding="utf-8"))
        assert got == expected
        pol = next(p for p in got["policies"] if p["chain"] == "INPUT")
        assert pol["packets"] == 120
        assert pol["bytes"] == 48000

    def test_iptctl_rule_counters_preserved(self) -> None:
        """Per-rule [pkts:bytes] suffixes must be exported."""
        restore = RESTORES / "counter-heavy.v4"
        expected = reference_simulate(restore, "seed-a")
        proc = simulate(restore, "seed-a", OUTPUT / "counter-probe.json")
        assert proc.returncode == 0
        got = json.loads((OUTPUT / "counter-probe.json").read_text(encoding="utf-8"))
        assert got == expected
        rule = next(r for r in got["rules"] if "dport 22" in r["spec"])
        assert rule["packets"] == 31
        assert rule["bytes"] == 2480

    def test_iptctl_conntrack_order_follows_chain(self) -> None:
        """Conntrack rules must stay in shuffled chain order, not sorted by spec."""
        restore = RESTORES / "ctstate-mix.v4"
        expected = reference_simulate(restore, "seed-b")
        proc = simulate(restore, "seed-b", OUTPUT / "ct-probe.json")
        assert proc.returncode == 0
        got = json.loads((OUTPUT / "ct-probe.json").read_text(encoding="utf-8"))
        assert got == expected
        assert got["conntrack_order"] == expected["conntrack_order"]
        assert [r["spec"] for r in got["conntrack_order"]] != sorted(
            r["spec"] for r in got["conntrack_order"]
        )

    def test_iptctl_seed_shuffle_changes_rule_index(self) -> None:
        """Different seeds must reorder -A lines within a table block."""
        restore = RESTORES / "nat-only-deps.v4"
        nat_orders = {
            seed: tuple(
                r["spec"]
                for r in reference_simulate(restore, seed)["rules"]
                if r["table"] == "nat"
            )
            for seed in SEEDS
        }
        assert len(set(nat_orders.values())) > 1

    def test_iptctl_ingest_writes_staging_schema(self) -> None:
        """Ingest must write staging_version and binding fields per staging-schema.md."""
        restore = RESTORES / "triple-order.v4"
        snap = STATE / "schema-probe.staging.json"
        proc = ingest(restore, snap)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        doc = json.loads(snap.read_text(encoding="utf-8"))
        required = {
            "staging_version",
            "restore_path",
            "restore",
            "restore_digest",
            "phase_config",
            "tables",
            "binding",
        }
        assert required <= set(doc.keys())
        assert doc["restore"] == "triple-order"
        assert merge_staging_path(snap).is_file()

    def test_iptctl_ingest_snapshot_matches_reference(self) -> None:
        """Ingest snapshot tables and phase_config must match the reference builder."""
        restore = RESTORES / "mangle-mark.v4"
        snap = STATE / "ref-staging.staging.json"

        with with_partial_patch(INGEST_CORE_GOLDEN):
            proc = ingest(restore, snap)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(snap.read_text(encoding="utf-8"))
            expect = reference_staging(restore)
            assert got["tables"] == expect["tables"]
            assert got["phase_config"] == expect["phase_config"]
            assert got["restore_digest"] == expect["restore_digest"]

    def test_iptctl_report_emit_snapshot_only_trap(self) -> None:
        """Golden ingest plus broken report_emit must diverge from reference on mark activation."""
        restore = RESTORES / "mangle-mark.v4"
        snap = STATE / "export-trap.staging.json"
        out = OUTPUT / "export-trap.json"

        with with_partial_patch({**INGEST_CORE_GOLDEN, "report_emit.sh": TRAPS / "broken_report_emit.sh"}):
            ing = ingest(restore, snap)
            assert ing.returncode == 0, ing.stderr
            exp = export_snapshot(snap, "7", out)
            assert exp.returncode == 0, exp.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_simulate(restore, "7")
            assert got != expect
            nat = [r for r in got["rules"] if r["table"] == "nat" and "-m mark" in r["spec"]]
            assert nat and not any(r["nat_active"] for r in nat)

    def test_iptctl_simulate_chains_ingest_export(self) -> None:
        """Simulate output must match ingest then export with the same restore and seed."""
        restore = RESTORES / "core-filter.v4"
        snap = STATE / "chain.staging.json"
        chained = OUTPUT / "chained.json"
        direct = OUTPUT / "direct-sim.json"
        ing = ingest(restore, snap)
        assert ing.returncode == 0, ing.stderr
        exp = export_snapshot(snap, SEEDS[0], chained)
        assert exp.returncode == 0, exp.stderr
        proc = simulate(restore, SEEDS[0], direct)
        assert proc.returncode == 0, proc.stderr
        assert json.loads(chained.read_text(encoding="utf-8")) == json.loads(
            direct.read_text(encoding="utf-8")
        )

    def test_iptctl_export_fails_when_merge_staging_missing(self) -> None:
        """Export must exit 4 when merge-staging sibling is absent."""
        restore = RESTORES / "core-filter.v4"
        snap = STATE / "no-merge.staging.json"
        out = OUTPUT / "no-merge.json"

        with with_partial_patch(
            {
                **INGEST_CORE_GOLDEN,
                "export_gate.sh": GOLDEN / "patch_lib_export_gate.sh",
                "report_emit.sh": GOLDEN / "patch_lib_report_emit.sh",
            },
        ):
            ing = ingest(restore, snap)
            assert ing.returncode == 0, ing.stderr
            merge_staging_path(snap).unlink()
            exp = export_snapshot(snap, "1", out)
            assert exp.returncode == 4, exp.stderr + exp.stdout
            assert not out.exists()

    def test_iptctl_export_rejects_tampered_plan_binding(self) -> None:
        """Guard must reject snapshots whose plan_digest was poisoned after ingest."""
        restore = RESTORES / "nat-only-deps.v4"
        snap = STATE / "tamper.staging.json"
        out = OUTPUT / "tamper.json"

        with with_partial_patch(
            {
                **INGEST_CORE_GOLDEN,
                "export_gate.sh": GOLDEN / "patch_lib_export_gate.sh",
                "report_emit.sh": GOLDEN / "patch_lib_report_emit.sh",
            },
        ):
            ing = ingest(restore, snap)
            assert ing.returncode == 0, ing.stderr
            doc = json.loads(snap.read_text(encoding="utf-8"))
            doc["binding"]["plan_digest"] = "deadbeef"
            snap.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
            exp = export_snapshot(snap, "1", out)
            assert exp.returncode == 4, exp.stderr + exp.stdout
            assert not out.exists()

    def test_iptctl_hidden_cross_table_mark_order(self) -> None:
        """Runtime restore with reversed table blocks must respect kernel commit order."""
        with tempfile.NamedTemporaryFile("w", suffix=".v4", delete=False, dir=STATE) as fh:
            fh.write(
                "*nat\n"
                ":PREROUTING ACCEPT [0:0]\n"
                "-A PREROUTING -m mark --mark 0x10/0xff -j DNAT --to-destination 10.0.0.2\n"
                "COMMIT\n"
                "*mangle\n"
                ":PREROUTING ACCEPT [0:0]\n"
                "-A PREROUTING -j MARK --set-mark 0x10\n"
                "COMMIT\n"
            )
            hidden = Path(fh.name)
        try:
            out = OUTPUT / "hidden-mark.json"
            proc = simulate(hidden, "99", out)
            assert proc.returncode == 0, proc.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            assert got["commit_order"] == ["mangle", "nat"]
            nat = next(r for r in got["rules"] if r["table"] == "nat")
            assert nat["nat_active"] is True
        finally:
            hidden.unlink(missing_ok=True)

    def test_iptctl_partial_commit_fix_still_wrong_order(self) -> None:
        """Injecting wrong table commit order must break NAT mark activation."""
        if not oracle_ready():
            pytest.skip("requires kernel table commit order in table_commit_order.sh")
        target = LIB / "table_commit_order.sh"
        saved = target.read_text(encoding="utf-8")
        try:
            _copy_lib_script(TRAPS / "broken_table_commit_order.sh", target)
            restore = RESTORES / "nat-only-deps.v4"
            proc = simulate(restore, "1", OUTPUT / "partial-commit.json")
            assert proc.returncode == 0
            got = json.loads((OUTPUT / "partial-commit.json").read_text(encoding="utf-8"))
            assert got["commit_order"] == ["nat", "mangle"]
            nat = [r for r in got["rules"] if r["table"] == "nat" and "-m mark" in r["spec"]]
            assert nat and not any(r["nat_active"] for r in nat)
        finally:
            target.write_text(saved, encoding="utf-8")

    def test_iptctl_partial_policy_fix_still_zeros_counters(self) -> None:
        """Injecting strip policy mode must drop :CHAIN baselines."""
        if not oracle_ready():
            pytest.skip("requires keep policy mode in chain_policy_mode.sh")
        target = LIB / "chain_policy_mode.sh"
        saved = target.read_text(encoding="utf-8")
        try:
            _copy_lib_script(TRAPS / "broken_chain_policy_mode.sh", target)
            restore = RESTORES / "core-filter.v4"
            proc = simulate(restore, "1", OUTPUT / "partial-policy.json")
            assert proc.returncode == 0
            got = json.loads((OUTPUT / "partial-policy.json").read_text(encoding="utf-8"))
            pol = next(p for p in got["policies"] if p["chain"] == "INPUT")
            assert pol["packets"] == 0 and pol["bytes"] == 0
        finally:
            target.write_text(saved, encoding="utf-8")

    def test_iptctl_partial_counters_fix_still_strips_rules(self) -> None:
        """Injecting strip rule-counter mode must zero per-rule counters."""
        if not oracle_ready():
            pytest.skip("requires keep rule-counter mode in rule_counter_mode.sh")
        target = LIB / "rule_counter_mode.sh"
        saved = target.read_text(encoding="utf-8")
        try:
            _copy_lib_script(TRAPS / "broken_rule_counter_mode.sh", target)
            restore = RESTORES / "counter-heavy.v4"
            proc = simulate(restore, "1", OUTPUT / "partial-counters.json")
            assert proc.returncode == 0
            got = json.loads((OUTPUT / "partial-counters.json").read_text(encoding="utf-8"))
            rule = next(r for r in got["rules"] if "dport 22" in r["spec"])
            assert rule["packets"] == 0 and rule["bytes"] == 0
        finally:
            target.write_text(saved, encoding="utf-8")

    def test_iptctl_partial_deps_fix_still_isolates_marks(self) -> None:
        """Injecting isolated mark mode must disable NAT activation."""
        if not oracle_ready():
            pytest.skip("requires linked mark mode in nat_mark_bridge.sh")
        target = LIB / "nat_mark_bridge.sh"
        saved = target.read_text(encoding="utf-8")
        try:
            _copy_lib_script(TRAPS / "broken_nat_mark_bridge.sh", target)
            restore = RESTORES / "mangle-mark.v4"
            proc = simulate(restore, "1", OUTPUT / "partial-deps.json")
            assert proc.returncode == 0
            got = json.loads((OUTPUT / "partial-deps.json").read_text(encoding="utf-8"))
            nat = [r for r in got["rules"] if r["table"] == "nat" and "-m mark" in r["spec"]]
            assert nat and not any(r["nat_active"] for r in nat)
        finally:
            target.write_text(saved, encoding="utf-8")

    def test_iptctl_partial_match_fix_still_lexical_ct(self) -> None:
        """Injecting lexical conntrack mode must sort ctstate rules by spec."""
        if not oracle_ready():
            pytest.skip("requires chain conntrack mode in ct_order_mode.sh")
        target = LIB / "ct_order_mode.sh"
        saved = target.read_text(encoding="utf-8")
        try:
            _copy_lib_script(TRAPS / "broken_ct_order_mode.sh", target)
            restore = RESTORES / "ctstate-mix.v4"
            proc = simulate(restore, "1", OUTPUT / "partial-match.json")
            assert proc.returncode == 0
            got = json.loads((OUTPUT / "partial-match.json").read_text(encoding="utf-8"))
            specs = [r["spec"] for r in got["conntrack_order"]]
            assert specs == sorted(specs)
            assert specs != [
                r["spec"]
                for r in reference_simulate(restore, "1")["conntrack_order"]
            ]
        finally:
            target.write_text(saved, encoding="utf-8")

    def test_iptctl_partial_golden_ingest_broken_export_still_wrong(self) -> None:
        """Golden ingest core with broken export must fail mark-linked NAT checks."""
        restore = RESTORES / "nat-only-deps.v4"
        snap = STATE / "partial-export.staging.json"
        out = OUTPUT / "partial-export.json"

        with with_partial_patch({**INGEST_CORE_GOLDEN, "report_emit.sh": TRAPS / "broken_report_emit.sh"}):
            ing = ingest(restore, snap)
            assert ing.returncode == 0, ing.stderr
            exp = export_snapshot(snap, "1", out)
            assert exp.returncode == 0, exp.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            expect = reference_simulate(restore, "1")
            assert got != expect

    def test_iptctl_partial_golden_phases_broken_staging_digest(self) -> None:
        """Golden phase modules with broken staging must fail merge-staging guard."""
        restore = RESTORES / "core-filter.v4"
        snap = STATE / "partial-staging.staging.json"
        out = OUTPUT / "partial-staging.json"

        with with_partial_patch(
            {
                **INGEST_CORE_GOLDEN,
                "merge_stage_writer.sh": TRAPS / "broken_merge_stage_writer.sh",
                "export_gate.sh": GOLDEN / "patch_lib_export_gate.sh",
                "report_emit.sh": GOLDEN / "patch_lib_report_emit.sh",
            },
        ):
            ing = ingest(restore, snap)
            assert ing.returncode == 0, ing.stderr
            exp = export_snapshot(snap, "1", out)
            assert exp.returncode == 4, exp.stderr + exp.stdout

    def test_iptctl_export_from_reference_staging(self) -> None:
        """Reference staging exported through golden export must match reference simulate."""
        restore = RESTORES / "triple-order.v4"
        snap = STATE / "ref-export.staging.json"
        out = OUTPUT / "ref-export.json"
        expect = reference_staging(restore)
        snap.write_text(json.dumps(expect, indent=2) + "\n", encoding="utf-8")
        merge = merge_staging_path(snap)
        merge.write_text(
            json.dumps(
                {
                    "staging_version": 1,
                    "merge_staging_digest": expect["binding"]["merge_staging_digest"],
                    "table_names": sorted(expect["tables"].keys()),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        with with_partial_patch(
            {
                "export_gate.sh": GOLDEN / "patch_lib_export_gate.sh",
                "report_emit.sh": GOLDEN / "patch_lib_report_emit.sh",
                "plan_binding.sh": GOLDEN / "patch_lib_plan_binding.sh",
            },
        ):
            exp = export_snapshot(snap, "seed-a", out)
            assert exp.returncode == 0, exp.stderr
            got = json.loads(out.read_text(encoding="utf-8"))
            assert got == reference_export_from_staging(expect, "seed-a")

    def test_iptctl_mark_visibility_lattice_doc_cited(self) -> None:
        """Mark visibility lattice contract must exist for content-derived phase resolution."""
        doc = Path(DOC_MARK_VISIBILITY_LATTICE)
        assert doc.is_file()
        text = doc.read_text(encoding="utf-8")
        assert "mark visibility lattice" in text.lower()
        assert "mangle" in text and "nat" in text

    def test_iptctl_content_derived_commit_order_mark_trap(self) -> None:
        """Static wrong commit order must fail mark activation even when ingest passes."""
        if not oracle_ready():
            pytest.skip("requires content-derived table commit order")
        restore = RESTORES / "mangle-mark.v4"
        proc = simulate(restore, "7", OUTPUT / "derived-order-probe.json")
        assert proc.returncode == 0
        got = json.loads((OUTPUT / "derived-order-probe.json").read_text(encoding="utf-8"))
        expect = reference_simulate(restore, "7")
        assert got == expect

    def test_iptctl_merge_staging_sibling_filename_rule(self) -> None:
        """Merge-staging sibling must append .merge-staging.json to snapshot filename."""
        restore = RESTORES / "triple-order.v4"
        snap = Path(DOC_FOO_STAGING)
        with with_partial_patch(INGEST_CORE_GOLDEN):
            proc = ingest(restore, snap)
            assert proc.returncode == 0, proc.stderr
        sibling = Path(DOC_FOO_MERGE)
        assert sibling.is_file()
        assert merge_staging_path(snap) == sibling

    def test_iptctl_export_guard_example_staging_doc_path(self) -> None:
        """export-guard-contract documents verify_staging_binding on a staging snapshot path."""
        assert Path(DOC_EXAMPLE_STAGING).name.endswith(".staging.json")

    def test_iptctl_tb3_cross_mark_trap_verifier_fixtures(self) -> None:
        """TB3 cross-mark restore under /opt/verifier-fixtures/tb3-restores/ enforces kernel order."""
        restore = HIDDEN_RESTORES / "cross-mark-trap.v4"
        if not restore.is_file():
            pytest.skip("TB3 restore not mounted")
        expected = reference_simulate(restore, "tb3-a")
        out = OUTPUT / "tb3-cross-mark.json"
        proc = simulate(restore, "tb3-a", out)
        assert proc.returncode == expected["exit_code"], proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        assert got == expected
        assert got["commit_order"] == ["mangle", "nat"]

    def test_iptctl_tb3_ctstate_shuffle_verifier_fixtures(self) -> None:
        """TB3 ctstate shuffle trap via /opt/verifier-fixtures/tb3-restores/ must match reference."""
        restore = HIDDEN_RESTORES / "ctstate-shuffle-trap.v4"
        if not restore.is_file():
            pytest.skip("TB3 restore not mounted")
        expected = reference_simulate(restore, "tb3-b")
        out = OUTPUT / "tb3-ctstate.json"
        proc = simulate(restore, "tb3-b", out)
        assert proc.returncode == expected["exit_code"], proc.stderr or proc.stdout
        got = json.loads(out.read_text(encoding="utf-8"))
        assert got == expected

    def test_iptctl_decoy_legacy_wrapper_not_on_hot_path(self) -> None:
        """Legacy restore wrapper decoy must exist but not be sourced by iptctl CLI."""
        decoy = APP / "decoy" / "legacy-restore-wrapper.sh"
        assert decoy.is_file()
        cli_text = CLI.read_text(encoding="utf-8")
        assert "legacy-restore-wrapper" not in cli_text
        assert "decoy" not in cli_text.lower()
