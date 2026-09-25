"""Bundled pamtrace behavioral tests — ingest load and export emit via subprocess."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pamtrace_harness import APP, CLI, LEDGER, invoke, run_pipeline, wipe
from pamtrace_independent_math import (
    reference_build_ledger,
    reference_expand_service,
    reference_expected_trace,
    reference_subject_groups,
    reference_walk_auth,
)


@pytest.fixture(autouse=True)
def _fresh():
    wipe()
    yield


def test_pt_pamtrace_cli_on_path():
    """pamtrace is installed on PATH at /app/bin/pamtrace."""
    assert Path("/app/bin/pamtrace").is_file()


def test_pt_sshd_basic_alice_success():
    """Alice receives a success verdict on the sshd-basic scenario."""
    out = run_pipeline("sshd-basic", "run-a1", service="sshd", subject="alice")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_expected_trace(Path("/app/fixtures/scenarios/sshd-basic"), "run-a1", "sshd-basic", "sshd", "alice")
    assert rep["steps"] == ref["steps"]
    assert rep["verdict"] == "success"
    assert rep["reason"] == "sufficient_success"


def test_pt_sshd_basic_bob_auth_err():
    """Bob fails auth on sshd-basic with contract-aligned reason codes."""
    out = run_pipeline("sshd-basic", "run-a2", service="sshd", subject="bob")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_expected_trace(Path("/app/fixtures/scenarios/sshd-basic"), "run-a2", "sshd-basic", "sshd", "bob")
    assert rep["verdict"] == ref["verdict"]
    assert rep["reason"] == ref["reason"]


def test_pt_ledger_fingerprint_matches_contract():
    """Compile writes a ledger fingerprint matching independent math."""
    run_pipeline("sshd-basic", "run-b1", service="sshd", subject="alice")
    got = json.loads(LEDGER.read_text(encoding="utf-8"))
    ref = reference_build_ledger(Path("/app/fixtures/scenarios/sshd-basic"), "run-b1", "sshd-basic")
    assert got["ledger_fingerprint"] == ref["ledger_fingerprint"]


def test_pt_login_include_expansion_order():
    """Nested includes preserve module order in the compiled ledger."""
    run_pipeline("login-nested-include", "run-c1", service="login", subject="dave")
    snap = json.loads(LEDGER.read_text(encoding="utf-8"))
    modules = snap["services"]["login"]["modules"]
    names = [m["module"] for m in modules]
    assert names.index("pam_env.so") < names.index("pam_faillock.so")
    assert names.index("pam_faillock.so") < names.index("pam_unix.so")


def test_pt_carol_requisite_failure_on_login():
    """Requisite module failure short-circuits Carol login with requisite_failure."""
    out = run_pipeline("login-nested-include", "run-c2", service="login", subject="carol")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_expected_trace(
        Path("/app/fixtures/scenarios/login-nested-include"),
        "run-c2",
        "login-nested-include",
        "login",
        "carol",
    )
    assert rep["reason"] == "requisite_failure"
    assert rep["steps"] == ref["steps"]
    assert rep["verdict"] == ref["verdict"]


def test_pt_multi_service_shared_sshd():
    """Shared multi-service bundle yields stable trace digest for sshd."""
    out = run_pipeline("multi-service-shared", "run-d1", service="sshd", subject="erin")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_expected_trace(
        Path("/app/fixtures/scenarios/multi-service-shared"),
        "run-d1",
        "multi-service-shared",
        "sshd",
        "erin",
    )
    assert rep["trace_digest"] == ref["trace_digest"]


def test_pt_ftp_service_extra_module():
    """FTP service stack length and verdict match reference simulation."""
    out = run_pipeline("multi-service-shared", "run-d2", service="ftp", subject="frank")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_expected_trace(
        Path("/app/fixtures/scenarios/multi-service-shared"),
        "run-d2",
        "multi-service-shared",
        "ftp",
        "frank",
    )
    assert len(rep["steps"]) == len(ref["steps"])
    assert rep["verdict"] == ref["verdict"]


def test_pt_substack_console_grace_requisite():
    """Console substack scenario stops on requisite failure for Grace."""
    out = run_pipeline("substack-nested", "run-e1", service="console", subject="grace")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_expected_trace(
        Path("/app/fixtures/scenarios/substack-nested"),
        "run-e1",
        "substack-nested",
        "console",
        "grace",
    )
    assert rep["reason"] == "requisite_failure"
    assert rep["steps"] == ref["steps"]


def test_pt_substack_no_duplicate_modules():
    """Substack expansion must not duplicate pam_listfile.so modules."""
    run_pipeline("substack-nested", "run-e2", service="console", subject="heidi")
    snap = json.loads(LEDGER.read_text(encoding="utf-8"))
    modules = snap["services"]["console"]["modules"]
    names = [m["module"] for m in modules]
    assert names.count("pam_listfile.so") == 1


def test_pt_trace_digest_stable_repeat():
    """Identical inputs produce identical trace_digest across repeated runs."""
    out1 = run_pipeline("sshd-basic", "run-f1", service="sshd", subject="alice")
    wipe()
    out2 = run_pipeline("sshd-basic", "run-f1", service="sshd", subject="alice")
    d1 = json.loads(out1.read_text(encoding="utf-8"))["trace_digest"]
    d2 = json.loads(out2.read_text(encoding="utf-8"))["trace_digest"]
    assert d1 == d2


def test_pt_emit_reads_ledger_not_load_only():
    """Emit uses the compiled ledger even when load metadata is overwritten."""
    run_pipeline("sshd-basic", "run-g1", service="sshd", subject="alice")
    load_meta = APP / "work" / "run-g1-load.json"
    load_meta.write_text("{}", encoding="utf-8")
    out = APP / "output" / "run-g1-reemit.json"
    proc = invoke([str(CLI), "emit", "--run-id", "run-g1", "--service", "sshd", "--subject", "alice", "--output", str(out)])
    assert proc.returncode == 0, proc.stderr
    assert json.loads(out.read_text(encoding="utf-8"))["steps"]


def test_pt_steps_sorted_by_execution_index():
    """Trace steps follow execution index order from the auth-path contract."""
    out = run_pipeline("login-nested-include", "run-h1", service="login", subject="dave")
    rep = json.loads(out.read_text(encoding="utf-8"))
    indices = [s["index"] for s in rep["steps"]]
    assert indices == sorted(indices)
    modules = [s["module"] for s in rep["steps"]]
    ref_modules = [m["module"] for m in reference_expected_trace(
        Path("/app/fixtures/scenarios/login-nested-include"), "run-h1", "login-nested-include", "login", "dave"
    )["steps"]]
    assert modules == ref_modules


def test_pt_subject_groups_nested_wheel():
    """Wheel membership closure includes nested parent groups for Alice."""
    run_pipeline("sudo-wheel", "run-i1", service="sudo", subject="alice")
    out = run_pipeline("sudo-wheel", "run-i1", service="sudo", subject="alice")
    rep = json.loads(out.read_text(encoding="utf-8"))
    subs = json.loads((Path("/app/fixtures/scenarios/sudo-wheel") / "subjects.json").read_text())
    assert rep["subject_groups"] == reference_subject_groups(subs, "alice")


def test_pt_sudo_bob_denied():
    """Bob is denied sudo access per module outcomes and group policy."""
    out = run_pipeline("sudo-wheel", "run-i2", service="sudo", subject="bob")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_expected_trace(Path("/app/fixtures/scenarios/sudo-wheel"), "run-i2", "sudo-wheel", "sudo", "bob")
    assert rep["verdict"] == ref["verdict"]


def test_pt_subprocess_load_stable_repeat():
    """Repeated load and compile invocations leave a usable ledger artifact."""
    for _ in range(2):
        proc = invoke([str(CLI), "load", "--scenario", "sshd-basic", "--run-id", "run-j1"])
        assert proc.returncode == 0, proc.stderr
    proc = invoke([str(CLI), "compile", "--run-id", "run-j1"])
    assert proc.returncode == 0, proc.stderr
    assert LEDGER.exists()


def test_pt_expand_service_common_auth_chain():
    """Include expansion yields four auth modules on the login service file."""
    login = Path("/app/fixtures/scenarios/login-nested-include/services/login")
    expanded = reference_expand_service(login)
    auth = [m for m in expanded if m.get("type") == "auth"]
    assert len(auth) == 4


def test_pt_walk_auth_sufficient_short_circuit():
    """Required failure blocks sufficient short-circuit in control-flow math."""
    mods = [
        {"type": "auth", "control": "required", "module": "pam_unix.so"},
        {"type": "auth", "control": "sufficient", "module": "pam_sss.so"},
    ]
    outcomes = {"pam_unix.so": {"*": "auth_err"}, "pam_sss.so": {"*": "success"}}
    got = reference_walk_auth(mods, outcomes, "alice")
    assert got["reason"] == "required_failure"


def test_pt_service_fingerprint_in_ledger():
    """Each compiled service records a non-empty service_fingerprint field."""
    run_pipeline("sshd-basic", "run-k1", service="sshd", subject="alice")
    snap = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert snap["services"]["sshd"]["service_fingerprint"]


def test_pt_decoy_not_in_trace_output():
    """Decoy module strings never appear in emitted trace JSON."""
    out = run_pipeline("sshd-basic", "run-l1", service="sshd", subject="alice")
    text = out.read_text(encoding="utf-8")
    assert "rhel6_pam_hint" not in text
    assert "decoy" not in text
