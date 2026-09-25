"""Behavioral verifier for ConnMan-style WiFi roam handoff repair."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from reference_roam import reference_export

APP = Path("/app")
CLI = "/app/scripts/connman-roamctl"
FIXTURES = APP / "fixtures"
SCENARIOS = FIXTURES / "scenarios"
OUTPUT = APP / "output"
RESET = APP / "scripts" / "reset-state.sh"
BROKEN = Path("/opt/verifier-broken-roam")
GOLDEN = Path(__file__).resolve().parent / "golden_modules"
HIDDEN_ROOT = Path(os.environ.get("TB3_SCENARIOS_DIR", "/opt/verifier-fixtures/roam-scenarios"))

CATALOG = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))
SEEDS = json.loads((FIXTURES / "seeds.json").read_text(encoding="utf-8"))["seeds"]
SCENARIO_IDS = list(CATALOG["scenarios"])

PROTECTED = [
    "fixtures/catalog.json",
    "fixtures/seeds.json",
    "docs/scenario-format.md",
    "docs/handoff-report-schema.md",
    "docs/fsm-states.md",
    "docs/scan-ledger-format.md",
    "docs/service-ranking.md",
    "docs/dhcp-renew.md",
]

MODULES = {
    "fsm": ("fsm.sh", "golden_fsm.sh"),
    "scan_ledger": ("scan_ledger.sh", "golden_scan_ledger.sh"),
    "service_rank": ("service_rank.sh", "golden_service_rank.sh"),
    "consent": ("consent.sh", "golden_consent.sh"),
    "dhcp": ("dhcp_hook.sh", "golden_dhcp_hook.sh"),
}


def _sha256(rel: str) -> str:
    return hashlib.sha256((APP / rel).read_bytes()).hexdigest()


PROTECTED_SHA256 = {rel: _sha256(rel) for rel in PROTECTED}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset_output() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def restore_broken_modules() -> None:
    """Restore the image-shipped broken roam modules from verifier snapshots."""
    for dest_name, _ in MODULES.values():
        shutil.copy2(BROKEN / dest_name, APP / "lib" / "roam" / dest_name)


def install_golden_modules(*, exclude: frozenset[str] = frozenset()) -> None:
    for key, (dest_name, golden_name) in MODULES.items():
        if key in exclude:
            continue
        shutil.copy2(GOLDEN / golden_name, APP / "lib" / "roam" / dest_name)


def scenario_path(scenario_id: str, root: Path = SCENARIOS) -> Path:
    return root / f"{scenario_id}.json"


def simulate_cli(
    scenario_id: str,
    seed: int,
    *,
    root: Path = SCENARIOS,
    export_suffix: str | None = None,
) -> subprocess.CompletedProcess[str]:
    path = scenario_path(scenario_id, root)
    tag = export_suffix if export_suffix is not None else str(seed)
    export_path = OUTPUT / f"{scenario_id}-{tag}.json"
    return run(
        [
            CLI,
            "simulate",
            "--scenario",
            str(path),
            "--seed",
            str(seed),
            "--export",
            str(export_path),
        ]
    )


def load_export(scenario_id: str, seed: int, *, suffix: str | None = None) -> dict:
    tag = suffix if suffix is not None else str(seed)
    return json.loads((OUTPUT / f"{scenario_id}-{tag}.json").read_text(encoding="utf-8"))


def load_export_after(
    scenario_id: str,
    seed: int,
    *,
    root: Path = SCENARIOS,
    suffix: str | None = None,
) -> dict:
    proc = simulate_cli(scenario_id, seed, root=root, export_suffix=suffix)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return load_export(scenario_id, seed, suffix=suffix)


@pytest.fixture(autouse=True)
def _reset_output_dir() -> None:
    """Clear /app/output before each test without undoing agent/oracle module fixes."""
    reset_output()


@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
@pytest.mark.parametrize("seed", SEEDS)
def test_catalog_simulate_matches_reference(scenario_id: str, seed: int) -> None:
    """Every catalog scenario and seed must match the independent reference export."""
    expected = reference_export(scenario_path(scenario_id), seed)
    got = load_export_after(scenario_id, seed)
    assert got == expected


def test_fixture_integrity() -> None:
    """Protected docs and catalog bytes must remain unchanged."""
    for rel, expected in PROTECTED_SHA256.items():
        assert _sha256(rel) == expected


def test_fsm_includes_disconnect_complete_before_scanning() -> None:
    """FSM must reach DISCONNECT_COMPLETE before SCANNING per /app/docs/fsm-states.md."""
    got = load_export_after("early-scan-trap", SEEDS[0])
    states = got["fsm_states"]
    assert "DISCONNECT_COMPLETE" in states
    assert states.index("DISCONNECT_COMPLETE") < states.index("SCANNING")


def test_partial_scan_coverage_does_not_credit_success() -> None:
    """Partial scan events must not be credited even when coverage is high."""
    got = load_export_after("partial-scan-trap", SEEDS[1])
    assert got["scan_credited"] is True
    partial_rows = [row for row in got["scan_ledger"] if row["event_type"] == "partial"]
    assert partial_rows
    assert all(not row["credited"] for row in partial_rows)


def test_security_tiebreak_prefers_stronger_security() -> None:
    """Equal preference and signal must break ties on security rank."""
    got = load_export_after("security-tiebreak", SEEDS[0])
    assert got["selected_service"]["security"] == "wpa3"
    assert got["handoff_success"] is True


def test_dhcp_renew_uses_target_gateway_after_credited_scan() -> None:
    """DHCP renew must use target_bss gateway after a credited scan."""
    got = load_export_after("stale-gateway-trap", SEEDS[2])
    assert got["scan_credited"] is True
    assert got["dhcp_gateway"] == "10.44.0.1"
    assert got["handoff_success"] is True


def test_hidden_network_requires_user_consent() -> None:
    """Hidden candidates must not win when user_consent_hidden is false."""
    got = load_export_after("hidden-consent-trap", SEEDS[0])
    assert got["selected_service"]["ssid"] == "DockRoam"
    assert got["selected_service"]["hidden"] is False
    assert got["handoff_success"] is True


def test_combo_handoff_integrates_all_layers() -> None:
    """Combo scenario requires FSM, scan, ranking, DHCP, and consent together."""
    got = load_export_after("combo-handoff", SEEDS[2])
    expected = reference_export(scenario_path("combo-handoff"), SEEDS[2])
    assert got == expected
    assert got["handoff_success"] is True


@pytest.mark.parametrize(
    "scenario_id",
    ["tb3-consent-granted", "tb3-partial-only"],
)
def test_tb3_hidden_scenarios_match_reference(scenario_id: str) -> None:
    """TB3_SCENARIOS_DIR fixtures must match the independent reference export."""
    seed = 11
    expected = reference_export(scenario_path(scenario_id, HIDDEN_ROOT), seed)
    got = load_export_after(scenario_id, seed, root=HIDDEN_ROOT, suffix=f"tb3-{seed}")
    assert got == expected


def test_tb3_partial_only_rejects_partial_scan_credit() -> None:
    """Hidden partial-only fixture must not credit partial scan coverage."""
    got = load_export_after("tb3-partial-only", 11, root=HIDDEN_ROOT, suffix="tb3-partial")
    assert got["scan_credited"] is False
    assert got["handoff_success"] is False


def test_partial_fix_without_fsm_still_fails_combo() -> None:
    """Fixing scan, rank, consent, and DHCP alone must not pass combo handoff."""
    restore_broken_modules()
    install_golden_modules(exclude=frozenset({"fsm"}))
    expected = reference_export(scenario_path("combo-handoff"), SEEDS[0])
    got = load_export_after("combo-handoff", SEEDS[0], suffix="partial-fsm")
    assert got != expected
    assert "DISCONNECT_COMPLETE" not in got["fsm_states"]


def test_partial_fix_without_dhcp_still_fails_gateway_trap() -> None:
    """Gateway selection must update independently of scan ledger fixes."""
    restore_broken_modules()
    install_golden_modules(exclude=frozenset({"dhcp"}))
    got = load_export_after("stale-gateway-trap", SEEDS[0], suffix="partial-dhcp")
    assert got["dhcp_gateway"] != "10.44.0.1"
    assert got["handoff_success"] is False


def test_partial_fix_without_scan_ledger_still_fails_partial_trap() -> None:
    """Scan ledger credit rules must not be bypassed by other module fixes."""
    restore_broken_modules()
    install_golden_modules(exclude=frozenset({"scan_ledger"}))
    expected = reference_export(scenario_path("tb3-partial-only", HIDDEN_ROOT), 11)
    got = load_export_after("tb3-partial-only", 11, root=HIDDEN_ROOT, suffix="partial-scan")
    assert got["scan_credited"] is True
    assert got != expected


def test_partial_fix_without_service_rank_still_fails_security_tiebreak() -> None:
    """Service ranking security tie-break is independent of FSM and DHCP fixes."""
    restore_broken_modules()
    install_golden_modules(exclude=frozenset({"service_rank"}))
    expected = reference_export(scenario_path("security-tiebreak"), SEEDS[0])
    got = load_export_after("security-tiebreak", SEEDS[0], suffix="partial-rank")
    assert got["selected_service"]["security"] == "wpa2"
    assert got != expected


def test_partial_fix_without_consent_and_rank_still_fails_hidden_trap() -> None:
    """Hidden consent gating must hold even when FSM, scan, and DHCP are fixed."""
    restore_broken_modules()
    install_golden_modules(exclude=frozenset({"service_rank", "consent"}))
    got = load_export_after("hidden-consent-trap", SEEDS[0], suffix="partial-hidden")
    assert got["selected_service"]["hidden"] is True
    assert got["handoff_success"] is False


def test_decoy_timeout_bump_does_not_repair_fsm_ordering() -> None:
    """Lengthening disconnect delay alone must not insert DISCONNECT_COMPLETE."""
    restore_broken_modules()
    timeout_src = APP / "lib" / "roam" / "timeout.sh"
    original = timeout_src.read_text(encoding="utf-8")
    try:
        timeout_src.write_text(
            original.replace("+ 5000", "+ 500000"),
            encoding="utf-8",
        )
        got = load_export_after("early-scan-trap", SEEDS[0], suffix="timeout-decoy")
        assert "DISCONNECT_COMPLETE" not in got["fsm_states"]
    finally:
        timeout_src.write_text(original, encoding="utf-8")
