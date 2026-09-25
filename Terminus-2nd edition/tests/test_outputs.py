"""Behavioral verifier for amavis quarantine spool release ledger pipeline."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from reference_replay import reference_run

APP = Path("/app")
OUTPUT = APP / "output"
CLI = "/app/bin/amavis-quarantine"
RESET = APP / "scripts/reset-state.sh"
LIB = APP / "lib"
GOLDEN_LIB = Path(__file__).resolve().parent / "golden_lib"
BROKEN_SNAPSHOT = Path(__file__).resolve().parent / "broken_lib"

LIB_MODULES = (
    "parse_log",
    "queue_route",
    "release",
    "ledger",
    "export",
    "ingest",
    "epoch",
    "staging",
    "policy",
    "custody",
    "pipeline",
)

CATALOG = json.loads((APP / "fixtures/catalog.json").read_text(encoding="utf-8"))
ALL_SCENARIOS = [row["name"] for row in CATALOG["scenarios"]]

VERIFIER_SEED = os.environ.get("VERIFIER_SEED", "amavis-quarantine-spool-release-ledger")
PROC_SEEDS = ("beta02", "gamma03")
PARTIAL_MODULES = LIB_MODULES


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def install_lib_module(src: Path, dest: Path) -> None:
    data = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    dest.write_bytes(data)


def install_golden_lib() -> None:
    for golden in GOLDEN_LIB.glob("golden_*.sh"):
        install_lib_module(golden, LIB / golden.name.removeprefix("golden_"))


def install_modules(only_broken: set[str]) -> None:
    for mod in LIB_MODULES:
        dest = LIB / f"{mod}.sh"
        if mod in only_broken:
            install_lib_module(BROKEN_SNAPSHOT / f"{mod}.sh", dest)
        else:
            install_lib_module(GOLDEN_LIB / golden_name(mod), dest)


def golden_name(mod: str) -> str:
    return f"golden_{mod}.sh"


def reconcile(scenario: str, *, seed: str = "alpha01", out: Path | None = None) -> subprocess.CompletedProcess[str]:
    target = out or (OUTPUT / f"{scenario}-{seed}.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    return run(
        [
            CLI,
            "reconcile",
            "--scenario",
            scenario,
            "--seed",
            seed,
            "--export",
            str(target),
        ]
    )


def load_export(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_matches_reference(scenario: str, seed: str = "alpha01") -> dict:
    out = OUTPUT / f"ref-{scenario}-{seed}.json"
    proc = reconcile(scenario, seed=seed, out=out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export(out)
    expect = reference_run(scenario, seed)
    assert got == expect
    return got


@pytest.fixture(autouse=True)
def _reset_between() -> None:
    reset()


def test_catalog_has_twelve_scenarios() -> None:
    """Fixture catalog lists every bundled reconcile scenario."""
    assert len(ALL_SCENARIOS) == 12
    assert "011-hold-token-gate" in ALL_SCENARIOS
    assert "012-custody-class-trap" in ALL_SCENARIOS


@pytest.mark.parametrize("scenario", ALL_SCENARIOS)
def test_scenario_matches_independent_reference(scenario: str) -> None:
    """Each bundled scenario export must match the Python reference implementation."""
    assert_matches_reference(scenario)


def test_ingest_writes_spool_manifest() -> None:
    """Reconcile must populate /app/state/spool-manifest.json during ingest."""
    out = OUTPUT / "manifest-check.json"
    proc = reconcile("001-single-spam", out=out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    manifest = json.loads((APP / "state/spool-manifest.json").read_text(encoding="utf-8"))
    assert len(manifest.get("messages", [])) == 1
    assert manifest["messages"][0]["quarantine_id"] == "04Rx-0001-sp"


def test_duplicate_release_is_idempotent() -> None:
    """Second identical release must increment duplicate_skipped without extra ledger sequence."""
    got = assert_matches_reference("003-duplicate-idempotent")
    assert got["releases_succeeded"] == 1
    assert got["duplicate_skipped"] == 1
    assert got["ledger_tail_sequence"] == 1


def test_failed_release_does_not_consume_sequence() -> None:
    """Missing spool file must not advance ledger_tail_sequence."""
    got = assert_matches_reference("006-missing-message")
    assert got["releases_failed"] == 1
    assert got["ledger_tail_sequence"] == 0


def test_pending_excludes_released_messages() -> None:
    """Export pending_in_spool must not list released quarantine ids."""
    got = assert_matches_reference("005-mixed-batch")
    assert got["pending_in_spool"]["spam"] == []
    assert got["pending_in_spool"]["virus"] == []


def test_parse_only_golden_still_fails_mixed_batch() -> None:
    """Golden parse_log alone must not pass multi-module mixed batch."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        install_modules({"parse_log"})
        out = OUTPUT / "trap-parse-only.json"
        proc = reconcile("005-mixed-batch", out=out)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_run("005-mixed-batch", "alpha01")
        assert got != expect
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_queue_route_only_golden_still_fails_virus() -> None:
    """Golden queue_route alone must not release virus-class messages correctly."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        install_modules({"queue_route"})
        out = OUTPUT / "trap-queue-only.json"
        proc = reconcile("002-single-virus", out=out)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_run("002-single-virus", "alpha01")
        assert got != expect
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_release_only_golden_still_fails_duplicate() -> None:
    """Golden release.sh alone must not make duplicate requests idempotent."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        install_modules({"release"})
        out = OUTPUT / "trap-release-only.json"
        proc = reconcile("003-duplicate-idempotent", out=out)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_run("003-duplicate-idempotent", "alpha01")
        assert got != expect
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_ledger_only_partial_still_records_failed_sequence() -> None:
    """Verifier partial ledger still records sequence numbers on failed attempts."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        install_modules({"ledger"})
        out = OUTPUT / "trap-ledger-only.json"
        proc = reconcile("006-missing-message", out=out)
        assert proc.returncode == 0
        ledger = json.loads((APP / "work/ledger.json").read_text(encoding="utf-8"))
        failed = [e for e in ledger.get("entries", []) if e.get("status") == "failed"]
        assert failed and all("sequence" in e for e in failed)
        install_golden_lib()
        reconcile("006-missing-message", out=OUTPUT / "trap-ledger-golden.json")
        ledger_ok = json.loads((APP / "work/ledger.json").read_text(encoding="utf-8"))
        failed_ok = [e for e in ledger_ok.get("entries", []) if e.get("status") == "failed"]
        assert failed_ok and all("sequence" not in e for e in failed_ok)
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_ingest_only_partial_still_leaves_empty_manifest() -> None:
    """Verifier partial ingest still leaves an empty spool manifest."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        install_modules({"ingest"})
        out = OUTPUT / "trap-ingest-only.json"
        proc = reconcile("001-single-spam", out=out)
        assert proc.returncode == 0
        manifest = json.loads((APP / "state/spool-manifest.json").read_text(encoding="utf-8"))
        assert manifest.get("messages", []) == []
        install_golden_lib()
        reconcile("001-single-spam", out=OUTPUT / "trap-ingest-golden.json")
        manifest_ok = json.loads((APP / "state/spool-manifest.json").read_text(encoding="utf-8"))
        assert len(manifest_ok.get("messages", [])) == 1
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_export_only_partial_still_lists_released_as_pending() -> None:
    """Broken export module must diverge from reference even when other modules are golden."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        install_modules({"export"})
        out = OUTPUT / "trap-export-only.json"
        proc = reconcile("001-single-spam", out=out)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_run("001-single-spam", "alpha01")
        assert got != expect
        assert got.get("custody_root", "") != expect.get("custody_root", "") or got.get(
            "prepare_fingerprint", ""
        ) != expect.get("prepare_fingerprint", "")
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_golden_lib_passes_smoke() -> None:
    """Installing all golden modules must satisfy the primary spam scenario."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        install_golden_lib()
        assert_matches_reference("001-single-spam")
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_hidden_swapped_queue_fixture() -> None:
    """Hidden fixture with cross-linked queue layout must match reference export."""
    hidden_root = Path("/opt/verifier-fixtures/hidden-swapped-queues")
    if not hidden_root.is_dir():
        pytest.skip("hidden fixture not mounted")
    seed = hashlib.sha256(f"{VERIFIER_SEED}-hidden".encode()).hexdigest()[:10]
    assert_matches_reference(str(hidden_root), seed=seed)


def test_queue_id_trap_requires_quarantine_field() -> None:
    """Scenario 004 must release using Quarantine-ID not Queue-ID."""
    got = assert_matches_reference("004-queue-id-trap")
    assert got["releases_succeeded"] == 1
    assert "04Rx-0004-qt" in json.dumps(got["release_log"])


def test_staging_only_golden_still_fails_meta_class() -> None:
    """Golden staging alone must not pass meta class trap when other modules stay partial."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        install_modules(set(PARTIAL_MODULES) - {"staging"})
        out = OUTPUT / "trap-staging-only.json"
        proc = reconcile("010-meta-class-trap", out=out)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_run("010-meta-class-trap", "alpha01")
        assert got != expect
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_staging_written_false_after_ingest() -> None:
    """Release staging must not mark staging_written true before export."""
    out = OUTPUT / "staging-flag.json"
    proc = reconcile("001-single-spam", out=out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    staging = json.loads((APP / "state/release-staging.json").read_text(encoding="utf-8"))
    assert staging.get("staging_written") is False
    assert staging.get("release_epoch") == 1


def test_release_epoch_starts_at_one() -> None:
    """First reconcile after reset must publish release_epoch 1 in export and staging."""
    got = assert_matches_reference("001-single-spam")
    assert got["release_epoch"] == 1
    epoch = json.loads((APP / "state/release-epoch.json").read_text(encoding="utf-8"))
    assert epoch.get("epoch") == 1


def test_cross_run_epoch_bumps_while_ledger_resets() -> None:
    """Second reconcile without reset must bump epoch while ledger_tail resets to one."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        install_golden_lib()
        out1 = OUTPUT / "epoch-run1.json"
        proc1 = reconcile("001-single-spam", out=out1)
        assert proc1.returncode == 0, proc1.stderr or proc1.stdout
        got1 = load_export(out1)
        assert got1["release_epoch"] == 1
        assert got1["ledger_tail_sequence"] == 1
        out2 = OUTPUT / "epoch-run2.json"
        proc2 = reconcile("001-single-spam", out=out2)
        assert proc2.returncode == 0, proc2.stderr or proc2.stdout
        got2 = load_export(out2)
        assert got2["release_epoch"] == 2
        assert got2["ledger_tail_sequence"] == 1
        staging = json.loads((APP / "state/release-staging.json").read_text(encoding="utf-8"))
        assert staging.get("release_epoch") == 2
        # Aliasing epoch to ledger_tail would wrongly yield 1 on the second run.
        assert got2["release_epoch"] != got2["ledger_tail_sequence"]
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_failed_only_scenario_still_bumps_epoch() -> None:
    """Missing-message scenario keeps ledger_tail at zero but still bumps release_epoch."""
    got = assert_matches_reference("006-missing-message")
    assert got["ledger_tail_sequence"] == 0
    assert got["release_epoch"] == 1


def test_epoch_only_golden_still_fails_mixed_batch() -> None:
    """Golden epoch alone must not satisfy mixed-batch export equality."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        install_modules(set(PARTIAL_MODULES) - {"epoch"})
        out = OUTPUT / "trap-epoch-only.json"
        proc = reconcile("005-mixed-batch", out=out)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_run("005-mixed-batch", "alpha01")
        assert got != expect
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_staging_without_epoch_field_breaks_export() -> None:
    """Broken staging that omits release_epoch must not match reference export."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        install_modules({"staging"})
        out = OUTPUT / "trap-staging-no-epoch.json"
        proc = reconcile("001-single-spam", out=out)
        assert proc.returncode == 0
        staging = json.loads((APP / "state/release-staging.json").read_text(encoding="utf-8"))
        assert "release_epoch" not in staging
        assert staging.get("staging_written") is True
        got = load_export(out)
        expect = reference_run("001-single-spam", "alpha01")
        assert got != expect
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_export_only_ignores_epoch_file() -> None:
    """Partial export that omits release_epoch must diverge from reference."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        install_modules({"export"})
        out = OUTPUT / "trap-export-no-epoch.json"
        proc = reconcile("006-missing-message", out=out)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_run("006-missing-message", "alpha01")
        assert got.get("release_epoch", -1) != expect["release_epoch"]
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_chained_trap_matches_reference() -> None:
    """Chained duplicate and missing release scenario must match reference."""
    got = assert_matches_reference("009-chained-trap")
    assert got["releases_succeeded"] == 2
    assert got["releases_failed"] == 1
    assert got["duplicate_skipped"] == 1


def test_meta_class_trap_matches_reference() -> None:
    """Meta stored_class must route locate via spool_subdir not request path alone."""
    assert_matches_reference("010-meta-class-trap")


@pytest.mark.parametrize("seed", PROC_SEEDS)
def test_seed_ordered_chained_trap_matches_reference(seed: str) -> None:
    """Non-alpha seeds must process chained trap rows in documented seed order."""
    assert_matches_reference("009-chained-trap", seed=seed)


def test_hidden_stored_class_mismatch_fixture() -> None:
    """Hidden meta class mismatch fixture must match reference export."""
    hidden_root = Path("/opt/verifier-fixtures/hidden-stored-class-mismatch")
    if not hidden_root.is_dir():
        pytest.skip("hidden fixture not mounted")
    seed = hashlib.sha256(f"{VERIFIER_SEED}-meta".encode()).hexdigest()[:10]
    assert_matches_reference(str(hidden_root), seed=seed)


def test_hidden_seed_order_virus_fixture() -> None:
    """Hidden multi-virus fixture with non-alpha seed must match reference ordering and epoch."""
    hidden_root = Path("/opt/verifier-fixtures/hidden-seed-order-virus")
    if not hidden_root.is_dir():
        pytest.skip("hidden fixture not mounted")
    seed = hashlib.sha256(f"{VERIFIER_SEED}-seedord".encode()).hexdigest()[:10]
    got = assert_matches_reference(str(hidden_root), seed=seed)
    assert got["release_epoch"] == 1
    assert got["releases_succeeded"] == 2
    assert got["releases_failed"] == 1


def test_011_hold_token_gate_matches_reference() -> None:
    """Hold-token gate allows correct token and rejects wrong token without sequence consume."""
    got = assert_matches_reference("011-hold-token-gate")
    assert got["releases_succeeded"] == 1
    assert got["releases_failed"] == 1
    assert got["ledger_tail_sequence"] == 1
    assert got["policy_digest"]


def test_policy_digest_on_staging_and_export() -> None:
    """Staging and export must publish matching policy_digest for hold-token fixtures."""
    out = OUTPUT / "policy-digest-check.json"
    proc = reconcile("011-hold-token-gate", out=out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export(out)
    staging = json.loads((APP / "state/release-staging.json").read_text(encoding="utf-8"))
    assert "policy_digest" in staging
    assert got.get("policy_digest") == staging["policy_digest"]
    assert got["policy_digest"] == reference_run("011-hold-token-gate", "alpha01")["policy_digest"]


def test_hidden_hold_token_fixture() -> None:
    """Hidden hold-token seed fixture must match reference (failure mode independent of meta-class)."""
    hidden_root = Path("/opt/verifier-fixtures/hidden-hold-token-seed")
    if not hidden_root.is_dir():
        pytest.skip("hidden fixture not mounted")
    seed = hashlib.sha256(f"{VERIFIER_SEED}-holdtok".encode()).hexdigest()[:10]
    got = assert_matches_reference(str(hidden_root), seed=seed)
    assert got["releases_succeeded"] == 1
    assert got["releases_failed"] == 1
    assert got["policy_digest"]


def test_policy_only_golden_still_fails_mixed_batch() -> None:
    """Golden policy alone must not satisfy mixed-batch export equality."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        install_modules(set(PARTIAL_MODULES) - {"policy"})
        out = OUTPUT / "trap-policy-only.json"
        proc = reconcile("005-mixed-batch", out=out)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_run("005-mixed-batch", "alpha01")
        assert got != expect
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_stack_without_policy_still_fails_011() -> None:
    """All golden modules except broken policy must still fail hold-token gate scenario."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        install_modules({"policy"})
        out = OUTPUT / "trap-no-policy-011.json"
        proc = reconcile("011-hold-token-gate", out=out)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_run("011-hold-token-gate", "alpha01")
        assert got != expect
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


@pytest.mark.parametrize("module", PARTIAL_MODULES)
def test_single_golden_module_insufficient(module: str) -> None:
    """Each single golden module patch alone leaves most catalog scenarios failing."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        broken = set(PARTIAL_MODULES) - {module}
        install_modules(broken)
        mismatches = 0
        for scenario in ALL_SCENARIOS:
            out = OUTPUT / f"golden-only-{module}-{scenario}.json"
            proc = reconcile(scenario, out=out)
            if proc.returncode != 0:
                mismatches += 1
                continue
            got = load_export(out)
            if got != reference_run(scenario, "alpha01"):
                mismatches += 1
        assert mismatches >= max(7, len(ALL_SCENARIOS) - 3), (
            f"single module {module} left too few mismatches ({mismatches}/{len(ALL_SCENARIOS)})"
        )
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_decoy_wrap_only_still_fails() -> None:
    """Patching legacy decoy wrap alone on the partial baseline must not satisfy reconcile."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    decoy_dir = LIB / "decoy"
    wrap = decoy_dir / "wrap.sh"
    try:
        install_modules(set(PARTIAL_MODULES))
        decoy_dir.mkdir(parents=True, exist_ok=True)
        wrap.write_text(
            "#!/usr/bin/env bash\nrelease_via_wrap() { RELEASE_OK=1; return 0; }\n",
            encoding="utf-8",
        )
        out = OUTPUT / "decoy-wrap.json"
        proc = reconcile("001-single-spam", out=out)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_run("001-single-spam", "alpha01")
        assert got != expect
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_custody_fields_on_export() -> None:
    """Export must publish prepare_fingerprint and class-aware custody_root."""
    got = assert_matches_reference("012-custody-class-trap")
    assert got["prepare_fingerprint"]
    assert got["custody_root"]
    assert got["releases_succeeded"] == 2
    seal = json.loads((APP / "state/prepare-seal.json").read_text(encoding="utf-8"))
    assert seal["prepare_fingerprint"] == got["prepare_fingerprint"]
    journal = (APP / "state/custody-journal.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(journal) == 2
    spam_only = hashlib.sha256(
        b"alpha01|04Rx-0012a-sp|1|spam"
    ).hexdigest()[:16]
    virus_wrong = hashlib.sha256(
        b"alpha01|04Rx-0012b-vi|2|virus"
    ).hexdigest()[:16]
    virus_right = hashlib.sha256(
        b"04Rx-0012b-vi|alpha01|2|virus"
    ).hexdigest()[:16]
    wrong_root = hashlib.sha256(f"{spam_only}\n{virus_wrong}".encode()).hexdigest()
    right_root = hashlib.sha256(f"{spam_only}\n{virus_right}".encode()).hexdigest()
    assert got["custody_root"] == right_root
    assert got["custody_root"] != wrong_root


def test_prepare_seal_and_custody_journal_paths() -> None:
    """Reconcile must materialize prepare-seal.json and custody-journal.jsonl under /app/state."""
    out = Path("/app/output/report.json")
    proc = reconcile("001-single-spam", out=out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert out.is_file()
    seal_path = Path("/app/state/prepare-seal.json")
    journal_path = Path("/app/state/custody-journal.jsonl")
    staging_path = Path("/app/state/release-staging.json")
    epoch_path = Path("/app/state/release-epoch.json")
    manifest_path = Path("/app/state/spool-manifest.json")
    assert seal_path.is_file()
    assert journal_path.is_file()
    assert staging_path.is_file()
    assert epoch_path.is_file()
    assert manifest_path.is_file()
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    assert seal["scenario"] == "001-single-spam"
    assert seal["prepare_fingerprint"]
    lines = [ln for ln in journal_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 1
    staging = json.loads(staging_path.read_text(encoding="utf-8"))
    assert "release_epoch" in staging
    epoch = json.loads(epoch_path.read_text(encoding="utf-8"))
    assert int(epoch.get("epoch", 0)) >= 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest.get("messages")


def test_prepare_commit_split_matches_reconcile() -> None:
    """Separate prepare then commit must match a single reconcile export."""
    out_split = OUTPUT / "split-012.json"
    out_one = OUTPUT / "one-012.json"
    prep = run([CLI, "prepare", "--scenario", "012-custody-class-trap", "--seed", "alpha01"])
    assert prep.returncode == 0, prep.stderr or prep.stdout
    seal = json.loads((APP / "state/prepare-seal.json").read_text(encoding="utf-8"))
    assert seal["scenario"] == "012-custody-class-trap"
    assert seal["prepare_fingerprint"]
    commit = run([CLI, "commit", "--export", str(out_split)])
    assert commit.returncode == 0, commit.stderr or commit.stdout
    split_doc = load_export(out_split)
    reset()
    one = reconcile("012-custody-class-trap", out=out_one)
    assert one.returncode == 0, one.stderr or one.stdout
    assert split_doc == load_export(out_one)


def test_commit_without_prepare_fails() -> None:
    """Commit with no prepare seal must fail closed."""
    out = OUTPUT / "no-seal.json"
    proc = run([CLI, "commit", "--export", str(out)])
    assert proc.returncode != 0


def test_custody_only_golden_still_fails_mixed_batch() -> None:
    """Golden custody alone must not satisfy mixed-batch export equality."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        install_modules(set(PARTIAL_MODULES) - {"custody"})
        out = OUTPUT / "trap-custody-only.json"
        proc = reconcile("005-mixed-batch", out=out)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_run("005-mixed-batch", "alpha01")
        assert got != expect
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_stack_without_custody_still_fails_012() -> None:
    """All golden modules except broken custody must still fail custody-class scenario."""
    saved = {p.name: p.read_text(encoding="utf-8") for p in LIB.glob("*.sh")}
    try:
        install_modules({"custody"})
        out = OUTPUT / "trap-no-custody-012.json"
        proc = reconcile("012-custody-class-trap", out=out)
        assert proc.returncode == 0
        got = load_export(out)
        expect = reference_run("012-custody-class-trap", "alpha01")
        assert got != expect
    finally:
        for name, content in saved.items():
            (LIB / name).write_text(content, encoding="utf-8")


def test_hidden_custody_class_fixture() -> None:
    """Hidden absolute-path custody mix must use basename fingerprint and virus receipt formula."""
    hidden_root = Path("/opt/verifier-fixtures/hidden-custody-class-mix")
    if not hidden_root.is_dir():
        pytest.skip("hidden fixture not mounted")
    seed = hashlib.sha256(f"{VERIFIER_SEED}-custody".encode()).hexdigest()[:10]
    got = assert_matches_reference(str(hidden_root), seed=seed)
    assert got["scenario"] == "hidden-custody-class-mix"
    assert got["releases_succeeded"] == 2
    assert got["prepare_fingerprint"]
    assert got["custody_root"]
    # Fingerprint must use basename, not absolute path.
    expect_fp = hashlib.sha256(
        f"hidden-custody-class-mix:{seed}:{got['policy_digest']}".encode()
    ).hexdigest()[:24]
    assert got["prepare_fingerprint"] == expect_fp
    wrong_fp = hashlib.sha256(
        f"{hidden_root}:{seed}:{got['policy_digest']}".encode()
    ).hexdigest()[:24]
    assert got["prepare_fingerprint"] != wrong_fp


def test_uniform_spam_receipt_formula_fails_virus() -> None:
    """Using spam receipt formula for virus must diverge from reference on 012."""
    from reference_replay import custody_receipt, custody_root_from_receipts

    spam_r = custody_receipt("alpha01", "04Rx-0012a-sp", 1, "spam")
    virus_uniform = hashlib.sha256(b"alpha01|04Rx-0012b-vi|2|virus").hexdigest()[:16]
    virus_correct = custody_receipt("alpha01", "04Rx-0012b-vi", 2, "virus")
    assert virus_uniform != virus_correct
    wrong = custody_root_from_receipts([spam_r, virus_uniform])
    right = custody_root_from_receipts([spam_r, virus_correct])
    assert wrong != right
    got = assert_matches_reference("012-custody-class-trap")
    assert got["custody_root"] == right
