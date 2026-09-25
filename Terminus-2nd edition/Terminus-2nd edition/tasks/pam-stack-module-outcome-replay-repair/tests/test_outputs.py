"""
Behavioral verifier for pamreplay stack replay repair.

Uses reference_replay.py for independent expected exit codes, env, and audit rows.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

from reference_replay import audit_path_for, flatten_stack, read_audit, replay_stack

APP = Path("/app")
FIXTURES = APP / "fixtures"
STACKS = FIXTURES / "stacks"
OUTPUT = APP / "output"
DOC_RUN_EXPORT = "/app/output/run.json"
DOC_RUN_AUDIT = "/app/output/run.audit.jsonl"
DOC_BASIC_LOGIN_AUDIT = "/app/output/001-basic-login.audit.jsonl"
CLI = "/app/bin/pamreplay"
RESET = APP / "scripts/reset-state.sh"
BROKEN = Path("/opt/verifier-broken-pam/lib")
GOLDEN = next(
    (p for p in (Path("/solution"), Path("/oracle/solution")) if (p / "golden_runner.sh").exists()),
    None,
)
REPAIR_MODULES = {
    "golden_stack.sh": "stack.sh",
    "golden_compose.sh": "compose.sh",
    "golden_runner.sh": "runner.sh",
    "golden_environment.sh": "environment.sh",
    "golden_audit.sh": "audit.sh",
    "golden_staging.sh": "staging.sh",
    "golden_outcome.sh": "outcome.sh",
    "golden_outcome_guard.sh": "outcome_guard.sh",
    "golden_export.sh": "export.sh",
}
STAGING_ARTIFACT = APP / "work" / "replay.staging.json"
COMPOSE_ARTIFACT = APP / "work" / "replay.compose.json"
OUTCOME_ARTIFACT = APP / "work" / "replay.outcome.json"
HIDDEN_FIXTURES = Path(__file__).resolve().parent / "hidden_fixtures"

CATALOG_STACKS = [
    "001-basic-login",
    "002-requisite-halt",
    "003-required-continue",
    "004-sufficient-skip",
    "005-include-flat",
    "006-include-nested",
    "007-env-gated",
    "008-audit-rollback",
    "009-phase-gate",
    "010-password-gate",
    "011-sufficient-after-fail",
    "012-deep-include",
    "013-auth-multi-env",
    "014-optional-fail",
    "015-account-env-immediate",
    "016-include-sequence",
    "017-depth-eight",
    "019-requisite-account-halt",
    "020-include-auth-module-order",
]


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd or APP),
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(autouse=True)
def reset_output() -> None:
    run(["bash", str(RESET)])


@pytest.fixture
def seed() -> str:
    return os.environ.get("VERIFIER_SEED", "verifier-run")


def user_for(seed: str, name: str) -> str:
    return f"{seed}-{name}"


def replay_cli(stack_name: str, username: str) -> subprocess.CompletedProcess[str]:
    stack_path = STACKS / f"{stack_name}.json"
    export_path = OUTPUT / f"{stack_name}.json"
    return run(
        [
            CLI,
            "replay",
            "--stack",
            str(stack_path),
            "--user",
            username,
            "--export",
            str(export_path),
        ]
    )


def load_export(name: str) -> dict:
    return json.loads((OUTPUT / f"{name}.json").read_text(encoding="utf-8"))


def export_only(export_path: Path) -> subprocess.CompletedProcess[str]:
    return run(
        [
            "bash",
            "-lc",
            "export PAMREPLAY_APP_ROOT=/app; "
            "source /app/lib/common.sh; "
            "source /app/lib/outcome.sh; "
            "source /app/lib/outcome_guard.sh; "
            "source /app/lib/export.sh; "
            f"pamreplay_write_export '{export_path}'",
        ]
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def strip_crlf(path: Path) -> None:
    path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n"))


@contextmanager
def partial_golden(modules: dict[str, str]):
    """Overlay broken baseline plus selected golden lib modules (oracle partial-trap probes)."""
    assert GOLDEN is not None
    assert BROKEN.is_dir(), "broken lib snapshot missing from image"
    lib_dir = APP / "lib"
    fixed_backup = {lib_dir / dest: (lib_dir / dest).read_bytes() for dest in REPAIR_MODULES.values()}
    touched: list[Path] = []
    try:
        for dest in REPAIR_MODULES.values():
            shutil.copy2(BROKEN / dest, lib_dir / dest)
            touched.append(lib_dir / dest)
        for golden_name, dest in modules.items():
            shutil.copy2(GOLDEN / golden_name, lib_dir / dest)
            touched.append(lib_dir / dest)
        for path in touched:
            strip_crlf(path)
        yield
    finally:
        for dest, content in fixed_backup.items():
            dest.write_bytes(content)


def test_manifest_integrity() -> None:
    """Fixture tree hashes must match image build manifest."""
    manifest_path = FIXTURES / "manifest.json"
    assert manifest_path.is_file(), "manifest.json missing"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for rel, expected in manifest["files"].items():
        path = FIXTURES / rel
        assert path.is_file(), rel
        assert sha256_file(path) == expected, rel


@pytest.mark.parametrize("stack_name", CATALOG_STACKS)
def test_replay_matches_reference(stack_name: str, seed: str) -> None:
    """CLI export, exit code, env, phases, and audit align with reference replay."""
    username = user_for(seed, stack_name)
    stack_path = str(STACKS / f"{stack_name}.json")
    export_path = str(OUTPUT / f"{stack_name}.json")

    expected = replay_stack(stack_path, username, export_path)
    proc = replay_cli(stack_name, username)
    assert proc.returncode == expected.exit_code, proc.stderr

    doc = load_export(stack_name)
    assert doc["stack"] == stack_path
    assert doc["user"] == username
    assert doc["exit_code"] == expected.exit_code
    assert doc["phases"] == expected.phases
    assert doc["environment"] == expected.environment
    assert doc["audit_path"] == audit_path_for(export_path)

    audit_file = Path(doc["audit_path"])
    assert audit_file.is_file()
    audit_rows = read_audit(audit_file)
    assert audit_rows == [r.to_dict() for r in expected.audit]
    if stack_name == "001-basic-login":
        assert doc["audit_path"] == DOC_BASIC_LOGIN_AUDIT
        assert Path(DOC_BASIC_LOGIN_AUDIT).is_file()


def test_export_run_json_writes_audit_sidecar(seed: str) -> None:
    """--export /app/output/run.json also writes /app/output/run.audit.jsonl per audit-format.md."""
    stack_path = str(STACKS / "001-basic-login.json")
    username = user_for(seed, "run-export")
    proc = run(
        [
            CLI,
            "replay",
            "--stack",
            stack_path,
            "--user",
            username,
            "--export",
            DOC_RUN_EXPORT,
        ]
    )
    assert proc.returncode == 0, proc.stderr
    assert Path(DOC_RUN_EXPORT).is_file()
    assert Path(DOC_RUN_AUDIT).is_file()
    doc = json.loads(Path(DOC_RUN_EXPORT).read_text(encoding="utf-8"))
    assert doc["audit_path"] == DOC_RUN_AUDIT


def test_requisite_runs_single_auth_module(seed: str) -> None:
    """Requisite failure must not execute later auth modules."""
    stack_name = "002-requisite-halt"
    username = user_for(seed, "req")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 1
    doc = load_export(stack_name)
    auth = next(p for p in doc["phases"] if p["phase"] == "auth")
    assert auth["modules_run"] == 1
    audit = read_audit(Path(doc["audit_path"]))
    auth_rows = [r for r in audit if r["phase"] == "auth"]
    assert len(auth_rows) == 1


def test_required_runs_all_auth_modules(seed: str) -> None:
    """Required failure still executes remaining auth modules."""
    stack_name = "003-required-continue"
    username = user_for(seed, "req-cont")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 1
    doc = load_export(stack_name)
    auth = next(p for p in doc["phases"] if p["phase"] == "auth")
    assert auth["modules_run"] == 3


def test_auth_failure_skips_account_phase(seed: str) -> None:
    """Account phase must not run when auth fails first."""
    stack_name = "009-phase-gate"
    username = user_for(seed, "gate")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 1
    doc = load_export(stack_name)
    phases = [p["phase"] for p in doc["phases"]]
    assert phases == ["auth"]
    assert doc["environment"] == {}


def test_auth_env_not_committed_on_failure(seed: str) -> None:
    """Auth-phase pam_env stays pending and account must not run when auth fails."""
    stack_name = "007-env-gated"
    username = user_for(seed, "env")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 1
    doc = load_export(stack_name)
    phases = [p["phase"] for p in doc["phases"]]
    assert phases == ["auth"]
    assert doc["phases"][0]["status"] == "fail"
    assert "TOKEN" not in doc["environment"]
    audit = read_audit(Path(doc["audit_path"]))
    assert all(row["phase"] == "auth" for row in audit)
    assert any(row["module"].endswith("pam_env.sh") for row in audit)
    assert not any(row["module"].endswith("pam_fail_account.sh") for row in audit)


def test_password_failure_skips_session(seed: str) -> None:
    """Session phase must not run when password fails after auth and account succeed."""
    stack_name = "010-password-gate"
    username = user_for(seed, "pw-gate")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 1
    doc = load_export(stack_name)
    phases = [p["phase"] for p in doc["phases"]]
    assert phases == ["auth", "account", "password"]
    assert "session" not in phases
    assert doc["environment"] == {}
    audit = read_audit(Path(doc["audit_path"]))
    assert not any(row["phase"] == "session" for row in audit)


def test_nested_include_within_depth(seed: str) -> None:
    """Nested includes within depth limit succeed."""
    stack_name = "006-include-nested"
    username = user_for(seed, "nest")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 0, proc.stderr
    doc = load_export(stack_name)
    assert doc["environment"].get("NESTED") == "deep"


def test_rollback_clears_committed_env(seed: str) -> None:
    """Failed stack rolls back committed env and records auth before account failure."""
    stack_name = "008-audit-rollback"
    username = user_for(seed, "rollback")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 1
    doc = load_export(stack_name)
    assert doc["environment"] == {}
    phases = [p["phase"] for p in doc["phases"]]
    assert phases == ["auth", "account"]
    assert phases[0] == "auth"
    audit = read_audit(Path(doc["audit_path"]))
    assert any(r["module"].endswith("pam_fail_account.sh") for r in audit)
    assert not any(r["phase"] == "session" for r in audit)


def test_per_run_user_token_in_export(seed: str) -> None:
    """Export records the per-run username token."""
    stack_name = "001-basic-login"
    username = user_for(seed, "token-check")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 0
    doc = load_export(stack_name)
    assert doc["user"] == username


def test_missing_stack_exits_nonzero(seed: str) -> None:
    """Missing stack path is a parse/usage failure."""
    export_path = OUTPUT / "missing.json"
    proc = run(
        [
            CLI,
            "replay",
            "--stack",
            str(STACKS / "no-such-stack.json"),
            "--user",
            user_for(seed, "missing"),
            "--export",
            str(export_path),
        ]
    )
    assert proc.returncode != 0
    assert proc.returncode != 1


def test_missing_required_flags_exit_nonzero() -> None:
    """Omitting --export must fail fast."""
    proc = run([CLI, "replay", "--stack", str(STACKS / "001-basic-login.json"), "--user", "x"])
    assert proc.returncode != 0


def test_flatten_reference_matches_contract() -> None:
    """Include expansion produces module entries for nested fixture."""
    flat = flatten_stack(STACKS / "005-include-flat.json")
    modules = [e["module"] for e in flat]
    assert "stubs/pam_env.sh" in modules
    assert any("ROLE=included" in e.get("args", []) for e in flat)


def test_sufficient_does_not_clear_required_failure(seed: str) -> None:
    """A later sufficient success must not rescue an earlier required auth failure."""
    stack_name = "011-sufficient-after-fail"
    username = user_for(seed, "sufficient-block")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 1
    doc = load_export(stack_name)
    assert doc["phases"] == [{"phase": "auth", "status": "fail", "modules_run": 2}]
    assert doc["environment"] == {}
    assert "account" not in [p["phase"] for p in doc["phases"]]


def test_deep_include_within_contract_depth(seed: str) -> None:
    """Five-level include chain must flatten and commit env from the deepest fragment."""
    stack_name = "012-deep-include"
    username = user_for(seed, "deep5")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 0, proc.stderr
    doc = load_export(stack_name)
    assert doc["environment"].get("DEPTH") == "five"


def test_auth_multi_env_commits_all_pending(seed: str) -> None:
    """Every auth-phase pam_env assignment must commit after successful auth."""
    stack_name = "013-auth-multi-env"
    username = user_for(seed, "multi-env")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 0, proc.stderr
    doc = load_export(stack_name)
    assert doc["environment"] == {"ALPHA": "1", "BETA": "2"}


def test_mutated_role_export_matches_reference(seed: str) -> None:
    """Per-run stack mutation must match independent reference replay."""
    base = json.loads((STACKS / "001-basic-login.json").read_text(encoding="utf-8"))
    token = hashlib.sha256(f"{seed}:role-mutate".encode()).hexdigest()[:8]
    mutated = copy.deepcopy(base)
    for entry in mutated["entries"]:
        if entry.get("module", "").endswith("pam_env.sh"):
            entry["args"] = [f"ROLE=mut-{token}"]
    username = user_for(seed, "mutated-role")
    with tempfile.TemporaryDirectory() as tmp:
        stack_path = Path(tmp) / "mutated-login.json"
        export_path = OUTPUT / "mutated-login.json"
        stack_path.write_text(json.dumps(mutated), encoding="utf-8")
        expected = replay_stack(str(stack_path), username, str(export_path))
        proc = run(
            [
                CLI,
                "replay",
                "--stack",
                str(stack_path),
                "--user",
                username,
                "--export",
                str(export_path),
            ]
        )
        assert proc.returncode == expected.exit_code, proc.stderr
        got = json.loads(export_path.read_text(encoding="utf-8"))
        assert got["environment"] == expected.environment
        assert got["phases"] == expected.phases
        assert got["exit_code"] == expected.exit_code


def test_optional_failure_does_not_fail_phase(seed: str) -> None:
    """Optional module failure must not fail the auth phase when a later required module succeeds."""
    stack_name = "014-optional-fail"
    username = user_for(seed, "optional")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 0, proc.stderr
    doc = load_export(stack_name)
    assert [p["phase"] for p in doc["phases"]] == ["auth", "account", "session"]
    auth = next(p for p in doc["phases"] if p["phase"] == "auth")
    assert auth["status"] == "ok"
    assert auth["modules_run"] == 2


def test_account_env_commits_immediately(seed: str) -> None:
    """Account-phase pam_env assignments commit immediately without auth pending rules."""
    stack_name = "015-account-env-immediate"
    username = user_for(seed, "acct-env")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 0, proc.stderr
    doc = load_export(stack_name)
    assert [p["phase"] for p in doc["phases"]] == ["auth", "account", "session"]
    assert doc["environment"] == {"SCOPE": "account"}


def test_include_sequence_preserves_fragment_order(seed: str) -> None:
    """Multiple sibling includes must expand inline preserving fragment module order."""
    stack_name = "016-include-sequence"
    username = user_for(seed, "seq")
    stack_path = str(STACKS / f"{stack_name}.json")
    export_path = str(OUTPUT / f"{stack_name}.json")
    expected = replay_stack(stack_path, username, export_path)
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 0, proc.stderr
    doc = load_export(stack_name)
    assert doc["phases"] == expected.phases
    assert doc["environment"] == expected.environment


def test_idempotent_replay_is_byte_stable(seed: str) -> None:
    """Two replays of the same stack must produce identical export and audit bytes."""
    stack_name = "013-auth-multi-env"
    username = user_for(seed, "idem")
    proc_a = replay_cli(stack_name, username)
    assert proc_a.returncode == 0, proc_a.stderr
    first_export = (OUTPUT / f"{stack_name}.json").read_bytes()
    first_audit = Path(load_export(stack_name)["audit_path"]).read_bytes()
    proc_b = replay_cli(stack_name, username)
    assert proc_b.returncode == 0, proc_b.stderr
    second_export = (OUTPUT / f"{stack_name}.json").read_bytes()
    second_audit = Path(load_export(stack_name)["audit_path"]).read_bytes()
    assert first_export == second_export
    assert first_audit == second_audit


def test_include_depth_exceeded_exits_two(seed: str) -> None:
    """Include nesting beyond the contract depth limit must exit 2."""
    export_path = OUTPUT / "overflow.json"
    proc = run(
        [
            CLI,
            "replay",
            "--stack",
            str(STACKS / "018-depth-overflow.json"),
            "--user",
            user_for(seed, "deep"),
            "--export",
            str(export_path),
        ]
    )
    assert proc.returncode == 2


def test_audit_seq_global_on_failed_stack(seed: str) -> None:
    """Audit seq must increase monotonically across phases on failed replays."""
    stack_name = "008-audit-rollback"
    username = user_for(seed, "audit-seq")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 1
    audit = read_audit(Path(load_export(stack_name)["audit_path"]))
    seqs = [row["seq"] for row in audit]
    assert seqs == [1, 2, 3]
    assert len(set(seqs)) == len(seqs)


def test_audit_seq_global_on_success_stack(seed: str) -> None:
    """Audit seq must stay global across phases on successful replays."""
    stack_name = "013-auth-multi-env"
    username = user_for(seed, "audit-seq-ok")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 0, proc.stderr
    audit = read_audit(Path(load_export(stack_name)["audit_path"]))
    seqs = [row["seq"] for row in audit]
    assert seqs == list(range(1, len(seqs) + 1))
    assert len(set(seqs)) == len(seqs)


def test_requisite_account_halts_same_phase(seed: str) -> None:
    """Requisite failure must stop the account phase before later account modules."""
    stack_name = "019-requisite-account-halt"
    username = user_for(seed, "acct-req")
    stack_path = str(STACKS / f"{stack_name}.json")
    export_path = str(OUTPUT / f"{stack_name}.json")
    expected = replay_stack(stack_path, username, export_path)
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 1
    doc = load_export(stack_name)
    assert doc["phases"] == expected.phases
    assert doc["environment"] == {}
    assert [p["phase"] for p in doc["phases"]] == ["auth", "account"]
    account = next(p for p in doc["phases"] if p["phase"] == "account")
    assert account["modules_run"] == 2
    audit = read_audit(Path(doc["audit_path"]))
    assert [row["seq"] for row in audit] == [1, 2, 3]
    assert "session" not in [row["phase"] for row in audit]


def test_depth_eight_boundary_requires_strict_depth_compare(seed: str) -> None:
    """Exactly eight include frames must flatten successfully with strict depth comparison."""
    stack_name = "017-depth-eight"
    username = user_for(seed, "depth-boundary")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 0, proc.stderr
    doc = load_export(stack_name)
    assert doc["environment"].get("DEPTH") == "eight"


def test_replay_writes_staging_artifact(seed: str) -> None:
    """Flatten stage must persist the staging artifact before execution."""
    stack_name = "001-basic-login"
    username = user_for(seed, "staging-artifact")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 0, proc.stderr
    assert COMPOSE_ARTIFACT.is_file(), "compose artifact missing"
    assert STAGING_ARTIFACT.is_file(), "staging artifact missing"
    staged = json.loads(STAGING_ARTIFACT.read_text(encoding="utf-8"))
    assert staged.get("stack_id") == stack_name
    assert isinstance(staged.get("entries"), list) and staged["entries"]


def test_replay_writes_outcome_snapshot(seed: str) -> None:
    """Successful replay must persist the outcome snapshot before export."""
    stack_name = "001-basic-login"
    username = user_for(seed, "outcome-snapshot")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 0, proc.stderr
    assert OUTCOME_ARTIFACT.is_file(), "outcome snapshot missing"
    snap = json.loads(OUTCOME_ARTIFACT.read_text(encoding="utf-8"))
    stack_path = str(STACKS / f"{stack_name}.json")
    assert snap.get("version") == 1
    assert snap.get("stack") == stack_path
    assert isinstance(snap.get("phases"), list) and snap["phases"]


def test_outcome_phases_follow_execution_order(seed: str) -> None:
    """Outcome snapshot phases must follow auth→account→password→session order."""
    stack_name = "019-requisite-account-halt"
    username = user_for(seed, "outcome-order")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 1
    snap = json.loads(OUTCOME_ARTIFACT.read_text(encoding="utf-8"))
    phase_names = [p["phase"] for p in snap["phases"]]
    assert phase_names == ["auth", "account"]
    assert phase_names != sorted(phase_names)


def test_outcome_exit_code_matches_phase_failure(seed: str) -> None:
    """Outcome snapshot exit_code must be non-zero when auth fails."""
    stack_name = "002-requisite-halt"
    username = user_for(seed, "outcome-exit")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 1, proc.stderr
    snap = json.loads(OUTCOME_ARTIFACT.read_text(encoding="utf-8"))
    assert snap["exit_code"] == 1
    assert load_export(stack_name)["exit_code"] == 1


def test_export_reads_outcome_snapshot_only(seed: str) -> None:
    """Export must reflect mutated outcome snapshot bytes, not re-evaluated staging."""
    stack_name = "001-basic-login"
    username = user_for(seed, "outcome-export")
    assert replay_cli(stack_name, username).returncode == 0
    snap = json.loads(OUTCOME_ARTIFACT.read_text(encoding="utf-8"))
    assert snap["phases"]
    snap["phases"][0]["modules_run"] = 999
    OUTCOME_ARTIFACT.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
    out_path = OUTPUT / "outcome-mutated.json"
    proc = export_only(out_path)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    doc = json.loads(out_path.read_text(encoding="utf-8"))
    assert doc["phases"][0]["modules_run"] == 999


def test_export_without_outcome_snapshot_fails(seed: str) -> None:
    """Export must fail when no outcome snapshot exists."""
    stack_name = "001-basic-login"
    username = user_for(seed, "no-outcome")
    assert replay_cli(stack_name, username).returncode == 0
    OUTCOME_ARTIFACT.unlink()
    proc = export_only(OUTPUT / "no-outcome-export.json")
    assert proc.returncode != 0


def test_compose_preserves_flatten_entry_order(seed: str) -> None:
    """Compose artifact entries must match flatten order (no phase/module sort)."""
    stack_name = "016-include-sequence"
    stack_path = STACKS / f"{stack_name}.json"
    username = user_for(seed, "compose-order")
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 0, proc.stderr
    flat_entries = flatten_stack(stack_path)
    composed = json.loads(COMPOSE_ARTIFACT.read_text(encoding="utf-8"))
    assert [e.get("module") for e in composed["entries"]] == [
        e.get("module") for e in flat_entries
    ]


def test_hidden_order_sensitive_sufficient_before_required(seed: str) -> None:
    """Hidden fixture: sufficient permit must run before required fail within auth."""
    stack_path = HIDDEN_FIXTURES / "order-sensitive.json"
    username = user_for(seed, "hidden-order")
    export_path = OUTPUT / "hidden-order-sensitive.json"
    expected = replay_stack(str(stack_path), username, str(export_path))
    proc = run(
        [
            CLI,
            "replay",
            "--stack",
            str(stack_path),
            "--user",
            username,
            "--export",
            str(export_path),
        ]
    )
    assert proc.returncode == expected.exit_code, proc.stderr
    got = json.loads(export_path.read_text(encoding="utf-8"))
    assert got["exit_code"] == 0
    assert got["phases"] == expected.phases
    assert got["environment"] == expected.environment


def test_include_auth_module_order_preserves_sufficient_first(seed: str) -> None:
    """Sibling includes must keep auth-phase module order; sufficient permit ends auth early."""
    stack_name = "020-include-auth-module-order"
    username = user_for(seed, "include-auth-order")
    stack_path = str(STACKS / f"{stack_name}.json")
    export_path = str(OUTPUT / f"{stack_name}.json")
    expected = replay_stack(stack_path, username, export_path)
    proc = replay_cli(stack_name, username)
    assert proc.returncode == 0, proc.stderr
    doc = load_export(stack_name)
    assert doc["phases"] == expected.phases
    auth = next(p for p in doc["phases"] if p["phase"] == "auth")
    assert auth["modules_run"] == 1
    audit = read_audit(Path(doc["audit_path"]))
    assert len(audit) == 2
    assert audit[0]["module"].endswith("pam_permit.sh")
    assert not any(row["module"].endswith("pam_fail_auth.sh") for row in audit)


def test_hidden_optional_sufficient_cannot_clear_required_failure(seed: str) -> None:
    """Hidden fixture: optional still runs; sufficient success must not clear required failure."""
    stack_path = HIDDEN_FIXTURES / "optional-sufficient-trap.json"
    username = user_for(seed, "hidden-optional-sufficient")
    export_path = OUTPUT / "hidden-optional-sufficient.json"
    expected = replay_stack(str(stack_path), username, str(export_path))
    proc = run(
        [
            CLI,
            "replay",
            "--stack",
            str(stack_path),
            "--user",
            username,
            "--export",
            str(export_path),
        ]
    )
    assert proc.returncode == expected.exit_code == 1, proc.stderr
    got = json.loads(export_path.read_text(encoding="utf-8"))
    assert got["phases"] == expected.phases
    assert got["phases"] == [{"phase": "auth", "status": "fail", "modules_run": 3}]
    assert "account" not in [p["phase"] for p in got["phases"]]
    audit = read_audit(Path(got["audit_path"]))
    assert len(audit) == 3
    assert [row["control"] for row in audit] == ["required", "optional", "sufficient"]


def test_staging_merge_poison_second_replay_in_run(seed: str) -> None:
    """Staging must replace prior entries; merged staging must not double module runs."""
    stack_name = "003-required-continue"
    username = user_for(seed, "staging-merge")
    proc_a = replay_cli(stack_name, username)
    assert proc_a.returncode == 1
    first_modules = next(p for p in load_export(stack_name)["phases"] if p["phase"] == "auth")["modules_run"]
    proc_b = replay_cli(stack_name, username)
    assert proc_b.returncode == 1
    second_modules = next(p for p in load_export(stack_name)["phases"] if p["phase"] == "auth")["modules_run"]
    assert first_modules == second_modules == 3


@pytest.mark.skipif(GOLDEN is None, reason="partial traps require oracle solution tree")
def test_partial_golden_staging_only_still_fails_include_auth_order(seed: str) -> None:
    """Staging repair alone must not restore include-expanded auth module order."""
    stack_name = "020-include-auth-module-order"
    username = user_for(seed, "trap-staging-auth-order")
    with partial_golden({"golden_staging.sh": "staging.sh"}):
        proc = replay_cli(stack_name, username)
        assert proc.returncode != 0 or next(
            p for p in load_export(stack_name)["phases"] if p["phase"] == "auth"
        )["modules_run"] != 1


@pytest.mark.skipif(GOLDEN is None, reason="partial traps require oracle solution tree")
def test_partial_golden_runner_only_still_fails_optional_sufficient_trap(seed: str) -> None:
    """Runner repair alone cannot satisfy export: broken export invents unrun account phase."""
    stack_path = HIDDEN_FIXTURES / "optional-sufficient-trap.json"
    username = user_for(seed, "trap-runner-optional-sufficient")
    export_path = OUTPUT / "hidden-runner-optional-sufficient.json"
    expected = replay_stack(str(stack_path), username, str(export_path))
    with partial_golden({"golden_runner.sh": "runner.sh"}):
        proc = run(
            [
                CLI,
                "replay",
                "--stack",
                str(stack_path),
                "--user",
                username,
                "--export",
                str(export_path),
            ]
        )
        got = json.loads(export_path.read_text(encoding="utf-8"))
        assert got["phases"] != expected.phases or proc.returncode != expected.exit_code


@pytest.mark.skipif(GOLDEN is None, reason="partial traps require oracle solution tree")
def test_partial_golden_compose_only_still_fails_hidden_order_sensitive(seed: str) -> None:
    """Compose repair alone must not restore control-flag order within a phase."""
    stack_path = HIDDEN_FIXTURES / "order-sensitive.json"
    username = user_for(seed, "trap-compose")
    export_path = OUTPUT / "hidden-compose-trap.json"
    expected = replay_stack(str(stack_path), username, str(export_path))
    with partial_golden({"golden_compose.sh": "compose.sh"}):
        proc = run(
            [
                CLI,
                "replay",
                "--stack",
                str(stack_path),
                "--user",
                username,
                "--export",
                str(export_path),
            ]
        )
        assert proc.returncode != expected.exit_code or json.loads(export_path.read_text())[
            "phases"
        ] != expected.phases


@pytest.mark.skipif(GOLDEN is None, reason="partial traps require oracle solution tree")
def test_partial_golden_runner_only_still_fails_global_audit_seq(seed: str) -> None:
    """Runner repair alone must not fix global audit sequencing."""
    stack_name = "008-audit-rollback"
    username = user_for(seed, "trap-runner")
    with partial_golden({"golden_runner.sh": "runner.sh"}):
        proc = replay_cli(stack_name, username)
        if proc.returncode == 0:
            audit = read_audit(Path(load_export(stack_name)["audit_path"]))
            seqs = [row["seq"] for row in audit]
            assert seqs != [1, 2, 3]
        else:
            assert proc.returncode == 2, proc.stderr


@pytest.mark.skipif(GOLDEN is None, reason="partial traps require oracle solution tree")
def test_partial_golden_stack_only_still_fails_requisite_halt(seed: str) -> None:
    """Stack repair alone must not short-circuit requisite auth failures."""
    stack_name = "002-requisite-halt"
    username = user_for(seed, "trap-stack")
    with partial_golden({"golden_stack.sh": "stack.sh"}):
        proc = replay_cli(stack_name, username)
        assert proc.returncode in (0, 2), proc.stderr
        if proc.returncode == 0:
            doc = load_export(stack_name)
            auth = next(p for p in doc["phases"] if p["phase"] == "auth")
            assert auth["modules_run"] != 1


@pytest.mark.skipif(GOLDEN is None, reason="partial traps require oracle solution tree")
def test_partial_golden_environment_only_still_fails_phase_gating(seed: str) -> None:
    """Environment repair alone must not enforce auth-first phase gating."""
    stack_name = "009-phase-gate"
    username = user_for(seed, "trap-env")
    with partial_golden({"golden_environment.sh": "environment.sh"}):
        proc = replay_cli(stack_name, username)
        assert proc.returncode in (0, 2), proc.stderr
        if proc.returncode == 0:
            phases = [p["phase"] for p in load_export(stack_name)["phases"]]
            assert phases != ["auth"]


@pytest.mark.skipif(GOLDEN is None, reason="partial traps require oracle solution tree")
def test_partial_golden_staging_only_still_fails_include_sequence(seed: str) -> None:
    """Staging repair alone must not fix runner phase order for include-expanded stacks."""
    stack_name = "016-include-sequence"
    username = user_for(seed, "trap-staging")
    stack_path = str(STACKS / f"{stack_name}.json")
    export_path = str(OUTPUT / f"{stack_name}.json")
    expected = replay_stack(stack_path, username, export_path)
    with partial_golden({"golden_staging.sh": "staging.sh"}):
        proc = replay_cli(stack_name, username)
        assert proc.returncode == 0, proc.stderr
        doc = load_export(stack_name)
        assert doc["phases"] != expected.phases or doc["environment"] != expected.environment


@pytest.mark.skipif(GOLDEN is None, reason="partial traps require oracle solution tree")
def test_partial_golden_export_only_still_fails_phase_report_order(seed: str) -> None:
    """Export repair alone must not fix execution-time phase gating."""
    stack_name = "010-password-gate"
    username = user_for(seed, "trap-export")
    with partial_golden({"golden_export.sh": "export.sh"}):
        proc = replay_cli(stack_name, username)
        assert proc.returncode != 0 or load_export(stack_name)["exit_code"] != 1


def _golden_except(*exclude: str) -> dict[str, str]:
    return {k: v for k, v in REPAIR_MODULES.items() if v not in exclude}


@pytest.mark.skipif(GOLDEN is None, reason="partial traps require oracle solution tree")
def test_partial_golden_outcome_guard_rejects_forced_zero_exit(seed: str) -> None:
    """Golden guard/export must reject outcome snapshots that force exit_code zero."""
    stack_name = "002-requisite-halt"
    username = user_for(seed, "trap-outcome-guard")
    with partial_golden(_golden_except("outcome.sh")):
        proc = replay_cli(stack_name, username)
        assert proc.returncode == 2, proc.stderr


@pytest.mark.skipif(GOLDEN is None, reason="partial traps require oracle solution tree")
def test_partial_broken_outcome_forces_cli_zero(seed: str) -> None:
    """Golden runner/export/guard cannot hide outcome.sh overwriting PAMREPLAY_EXIT_CODE."""
    stack_name = "002-requisite-halt"
    username = user_for(seed, "trap-outcome-cli")
    with partial_golden(_golden_except("outcome.sh", "outcome_guard.sh")):
        proc = replay_cli(stack_name, username)
        assert proc.returncode == 0, proc.stderr
        expected = replay_stack(str(STACKS / f"{stack_name}.json"), username, str(OUTPUT / f"{stack_name}.json"))
        assert expected.exit_code == 1


@pytest.mark.skipif(GOLDEN is None, reason="partial traps require oracle solution tree")
def test_partial_broken_outcome_guard_noop_allows_alphabetical_phases(seed: str) -> None:
    """Broken guard must not reject alphabetically sorted outcome phases."""
    stack_name = "019-requisite-account-halt"
    username = user_for(seed, "trap-guard-order")
    with partial_golden(_golden_except("outcome.sh", "outcome_guard.sh")):
        proc = replay_cli(stack_name, username)
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(OUTCOME_ARTIFACT.read_text(encoding="utf-8"))
        assert [p["phase"] for p in snap["phases"]] == ["account", "auth"]


@pytest.mark.skipif(GOLDEN is None, reason="partial traps require oracle solution tree")
def test_partial_golden_runner_outcome_only_fails_export_snapshot_trap(seed: str) -> None:
    """Golden runner/outcome without export binding must fail outcome snapshot export."""
    stack_name = "010-password-gate"
    username = user_for(seed, "trap-outcome-export")
    stack_path = str(STACKS / f"{stack_name}.json")
    export_path = str(OUTPUT / f"{stack_name}.json")
    expected = replay_stack(stack_path, username, export_path)
    with partial_golden({"golden_runner.sh": "runner.sh", "golden_outcome.sh": "outcome.sh"}):
        proc = replay_cli(stack_name, username)
        assert proc.returncode != expected.exit_code or load_export(stack_name) != {
            "stack": expected.stack,
            "user": expected.user,
            "exit_code": expected.exit_code,
            "phases": expected.phases,
            "environment": expected.environment,
            "audit_path": audit_path_for(export_path),
        }
