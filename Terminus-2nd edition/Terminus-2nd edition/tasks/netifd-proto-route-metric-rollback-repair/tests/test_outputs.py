"""Behavioral verifier for netifd-ctl route metric rollback repair."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from reference_netifd import (
    expected_teardown_order,
    reference_export,
    route_binding,
)

APP = Path("/app")
CLI = "/app/bin/netifd-ctl"
FIXTURES = APP / "fixtures" / "scenarios"
OUTPUT = APP / "output"
SNAPSHOT = APP / "state" / "netifd.snapshot.json"
CATALOG = json.loads((APP / "fixtures" / "catalog.json").read_text(encoding="utf-8"))
RESET = APP / "scripts" / "reset-state.sh"
TEARDOWN_LOG = APP / "harness" / "runtime" / "teardown.log"
HIDDEN_ROOT = Path(os.environ.get("TB3_FIXTURES_DIR", "/opt/verifier-fixtures/netifd"))

PROTECTED = [
    "fixtures/catalog.json",
    "fixtures/scenarios/default-route.json",
    "docs/proto-contract.md",
    "docs/staging-snapshot.md",
    "docs/export-schema.md",
]


def _sha256(rel: str) -> str:
    return hashlib.sha256((APP / rel).read_bytes()).hexdigest()


PROTECTED_SHA256 = {rel: _sha256(rel) for rel in PROTECTED}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def ctl_apply(name: str, *, root: Path = FIXTURES) -> subprocess.CompletedProcess[str]:
    return run([CLI, "apply", "--scenario", name, "--fixtures-root", str(root)])


def ctl_reload(name: str, *, root: Path = FIXTURES) -> subprocess.CompletedProcess[str]:
    return run([CLI, "reload", "--scenario", name, "--fixtures-root", str(root)])


def ctl_teardown(name: str, *, root: Path = FIXTURES) -> subprocess.CompletedProcess[str]:
    return run([CLI, "teardown", "--scenario", name, "--fixtures-root", str(root)])


def ctl_export(out_path: Path) -> subprocess.CompletedProcess[str]:
    return run([CLI, "export", "--output", str(out_path)])


def pipeline_export(name: str, *, reload: bool = False, teardown: bool = False, root: Path = FIXTURES) -> dict:
    if reload:
        proc = ctl_reload(name, root=root)
    else:
        proc = ctl_apply(name, root=root)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    if teardown:
        proc = ctl_teardown(name, root=root)
        assert proc.returncode == 0, proc.stderr or proc.stdout
    out = OUTPUT / f"{name}-export.json"
    proc = ctl_export(out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return json.loads(out.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _reset_output() -> None:
    """Clear harness runtime and output before each test."""
    reset()
    OUTPUT.mkdir(parents=True, exist_ok=True)


@pytest.mark.parametrize("scenario_name", [s["name"] for s in CATALOG["scenarios"]])
def test_catalog_scenario_export_matches_reference(scenario_name: str) -> None:
    """Each bundled catalog scenario export must match the independent reference."""
    scenario_path = FIXTURES / f"{scenario_name}.json"
    got = pipeline_export(scenario_name)
    want = reference_export(scenario_path)
    assert got == want


def test_staging_snapshot_exists_after_apply() -> None:
    """Apply must persist /app/state/netifd.snapshot.json with route_binding."""
    proc = ctl_apply("default-route")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert SNAPSHOT.is_file(), "missing staging snapshot"
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap.get("schema") == 1
    assert snap.get("route_binding") == route_binding(snap)


def test_default_route_uses_kernel_assigned_metric() -> None:
    """Rollback after teardown must restore routes with kernel-assigned metric."""
    routes_file = APP / "harness" / "runtime" / "routes.json"
    proc = ctl_apply("default-route")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    proc = ctl_teardown("default-route")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    routes = json.loads(routes_file.read_text(encoding="utf-8"))
    assert len(routes) == 1
    assert routes[0]["metric"] == 237


def test_hotplug_burst_deduplicates_addresses() -> None:
    """Burst hotplug adds must collapse to one address row."""
    got = pipeline_export("hotplug-burst")
    assert len(got["addresses"]) == 1
    assert got["addresses"][0]["addr"] == "192.0.2.44/32"


def test_pd_reload_releases_lease_before_reacquire() -> None:
    """Reload must leave exactly one PD lease for the iface."""
    proc = ctl_apply("pd-reload")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    proc = ctl_reload("pd-reload")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    out = OUTPUT / "pd-reload-export.json"
    proc = ctl_export(out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads(out.read_text(encoding="utf-8"))
    assert len(got["pd_leases"]) == 1
    assert got["pd_leases"][0]["id"] == "pd-wan-1"


def test_teardown_acknowledges_link_before_default_route_delete() -> None:
    """Teardown must log link_down and link_down_ack before route_del_default."""
    proc = ctl_apply("teardown-order")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    proc = ctl_teardown("teardown-order")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    steps = [line for line in TEARDOWN_LOG.read_text(encoding="utf-8").splitlines() if line]
    for step in expected_teardown_order():
        assert step in steps, f"missing teardown step {step}"
    assert steps.index("link_down") < steps.index("link_down_ack") < steps.index("route_del_default")


def test_snapshot_rules_committed_after_apply() -> None:
    """Staging snapshot must record rules_committed true after apply."""
    got = pipeline_export("rule-commit")
    assert got["rules_committed"] is True
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["rules_committed"] is True


def test_export_rejects_tampered_route_binding() -> None:
    """Export must fail when snapshot route_binding no longer matches payload."""
    proc = ctl_apply("default-route")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    snap["route_binding"] = "0" * 64
    SNAPSHOT.write_text(json.dumps(snap, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out = OUTPUT / "tampered-export.json"
    proc = ctl_export(out)
    assert proc.returncode != 0


def test_export_preserves_route_order() -> None:
    """Export must preserve staged route order rather than sorting by destination."""
    proc = ctl_apply("rule-commit")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    want = reference_export(FIXTURES / "rule-commit.json")
    out = OUTPUT / "order-export.json"
    proc = ctl_export(out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads(out.read_text(encoding="utf-8"))
    assert got["routes"] == want["routes"]


def test_hidden_reload_metric_trap() -> None:
    """Hidden fixture reload-metric-trap must use kernel bonus 99 on metric 80."""
    hidden = HIDDEN_ROOT / "scenarios" / "reload-metric-trap.json"
    assert hidden.is_file(), "hidden fixtures must be generated by verifier test.sh"
    got = pipeline_export("reload-metric-trap", root=HIDDEN_ROOT / "scenarios")
    assert got["routes"][0]["metric"] == 179
    want = reference_export(hidden)
    assert got == want


def test_protected_files_unchanged() -> None:
    """Bundled fixtures and contract docs must not be edited by the agent."""
    for rel, digest in PROTECTED_SHA256.items():
        assert _sha256(rel) == digest, f"protected file modified: {rel}"


def test_teardown_export_updates_teardown_log_in_snapshot() -> None:
    """After teardown, export must match reference with full harness event log."""
    scenario_path = FIXTURES / "teardown-order.json"
    proc = ctl_apply("teardown-order")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    proc = ctl_teardown("teardown-order")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert SNAPSHOT.is_file(), "teardown must rewrite staging snapshot"
    out = OUTPUT / "teardown-export.json"
    proc = ctl_export(out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads(out.read_text(encoding="utf-8"))
    want = reference_export(scenario_path, teardown=True)
    assert got == want
    assert "rules_commit" in got["teardown_log"]
    assert got["teardown_log"].index("route_del_default") > got["teardown_log"].index("link_down_ack")
