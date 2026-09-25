"""Behavioral verifier for offlineimap-audit maxage sync window."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

APP = Path("/app")
TOOLS = APP / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from offlineimap_model import (  # noqa: E402
    APP,
    HIDDEN_CASE_KINDS,
    LEDGER_PATH,
    PROTECTED_SHA256,
    SNAPSHOT_PATH,
    SYNC_RUN_PATH,
    filter_folders,
    load_manifest,
    maxage_cutoff,
    sha256_file,
    simulate_sync_export,
    select_messages,
    validate_folder_snapshot,
    validate_sync_run,
)
CLI = "/app/bin/offlineimap-audit"
FIXTURES = APP / "fixtures"
SCENARIOS = FIXTURES / "scenarios"
OUTPUT = APP / "output"
RESET = APP / "scripts" / "reset-state.sh"
BUILD_HIDDEN = Path(os.environ.get("TEST_DIR", "/tests")) / "build_hidden_fixtures.py"
CATALOG = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))


def _sha256(rel: str) -> str:
    return sha256_file(APP / rel)


def run(cmd: list[str], *, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def scenario_dir(name: str, root: Path = SCENARIOS) -> Path:
    return root / name


def sync_cli(
    name: str,
    *,
    root: Path = SCENARIOS,
    catalog: dict | None = None,
    dry_run: bool = False,
    export_name: str | None = None,
    env: dict | None = None,
    imap_meta: Path | None = None,
    folder_rules: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    cat = catalog or CATALOG
    entry = next(s for s in cat["scenarios"] if s["name"] == name)
    sdir = scenario_dir(name, root)
    export = OUTPUT / (export_name or f"{name}.json")
    cmd = [
        CLI,
        "sync",
        "--mailbox-dir",
        str(sdir),
        "--imap-meta",
        str(imap_meta or (sdir / "imap-meta.json")),
        "--folder-rules",
        str(folder_rules or (sdir / "folder.rules")),
        "--reference-epoch",
        str(entry["reference_epoch"]),
        "--maxage-sec",
        str(entry["maxage_sec"]),
        "--tz-offset",
        str(entry["tz_offset"]),
        "--export",
        str(export),
    ]
    if dry_run:
        cmd.append("--dry-run")
    return run(cmd, env=env)


def load_export(name: str, export_name: str | None = None) -> dict:
    path = OUTPUT / (export_name or f"{name}.json")
    return json.loads(path.read_text(encoding="utf-8"))


def scenario_meta(name: str, *, root: Path = SCENARIOS) -> tuple[dict, str]:
    sdir = scenario_dir(name, root)
    meta = json.loads((sdir / "imap-meta.json").read_text(encoding="utf-8"))
    rules_text = (sdir / "folder.rules").read_text(encoding="utf-8")
    return meta, rules_text


def scenario_name_with_rule(rule_line: str, *, root: Path = SCENARIOS) -> str:
    for entry in CATALOG["scenarios"]:
        rules_path = root / entry["name"] / "folder.rules"
        if rule_line in rules_path.read_text(encoding="utf-8").splitlines():
            return str(entry["name"])
    raise AssertionError(f"no scenario found with rule {rule_line!r}")


def verifier_scenario(kind: str) -> tuple[dict, Path]:
    fixtures_root = Path(os.environ.get("TB3_FIXTURES_DIR", "/opt/verifier-fixtures/offlineimap"))
    verifier_catalog = json.loads((fixtures_root / "catalog.json").read_text(encoding="utf-8"))
    expected_name = HIDDEN_CASE_KINDS[kind]
    entry = next(
        s
        for s in verifier_catalog["scenarios"]
        if s.get("kind") == kind and s.get("name") == expected_name
    )
    return entry, fixtures_root / "scenarios"


def ledger_rows() -> list[tuple[str, int, int]]:
    conn = sqlite3.connect(LEDGER_PATH)
    rows = conn.execute(
        "SELECT folder, uidvalidity, high_uid FROM folder_cache ORDER BY folder"
    ).fetchall()
    conn.close()
    return [(str(folder), int(uidvalidity), int(high_uid)) for folder, uidvalidity, high_uid in rows]


@pytest.fixture(scope="session", autouse=True)
def _prepare_runtime() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    build_proc = run(["make", "-C", str(APP), "install"])
    assert build_proc.returncode == 0, build_proc.stderr or build_proc.stdout
    hidden_proc = run(["/opt/verifier-venv/bin/python3", str(BUILD_HIDDEN)])
    assert hidden_proc.returncode == 0, hidden_proc.stderr or hidden_proc.stdout


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset()


@pytest.mark.parametrize("scenario_name", [s["name"] for s in CATALOG["scenarios"]])
def test_bundled_export_matches_reference(scenario_name: str) -> None:
    """Each catalog scenario export must match independent reference math."""
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == scenario_name)
    proc = sync_cli(scenario_name)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export(scenario_name)
    expect = simulate_sync_export(
        scenario_dir(scenario_name),
        entry["reference_epoch"],
        entry["maxage_sec"],
        entry["tz_offset"],
    )
    assert got == expect


def test_folder_snapshot_digest_selected_only() -> None:
    """Staging snapshot digest covers selected folders only."""
    scenario_name = scenario_name_with_rule("exclude Work/Archive")
    proc = sync_cli(scenario_name)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    snap = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    meta, rules_text = scenario_meta(scenario_name)
    validate_folder_snapshot(snap, meta, rules_text)
    selected = [f["name"] for f in snap["folders"] if f["selected"]]
    assert "Work/Archive" not in selected
    assert "Work/Active" in selected


@pytest.mark.parametrize("scenario_name", [s["name"] for s in CATALOG["scenarios"]])
def test_folder_snapshot_schema_matches_docs(scenario_name: str) -> None:
    """folder-snapshot.json must satisfy staging-snapshot.md schema version 1."""
    proc = sync_cli(scenario_name)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    snap = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    meta, rules_text = scenario_meta(scenario_name)
    validate_folder_snapshot(snap, meta, rules_text)


def test_work_exclude_drops_archive_messages() -> None:
    """Excluded archive folder must not contribute bytes."""
    scenario_name = scenario_name_with_rule("exclude Work/Archive")
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == scenario_name)
    proc = sync_cli(scenario_name)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    doc = load_export(scenario_name)
    expect = simulate_sync_export(
        scenario_dir(scenario_name),
        entry["reference_epoch"],
        entry["maxage_sec"],
        entry["tz_offset"],
    )
    assert doc == expect
    assert "Work/Archive" not in doc["folders"]
    assert doc["synced_bytes"] != doc["synced_messages"]


def test_basic_inbox_byte_sum_not_message_count() -> None:
    """synced_bytes must sum sizes, not mirror message count."""
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == "basic-inbox")
    proc = sync_cli("basic-inbox")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    doc = load_export("basic-inbox")
    expect = simulate_sync_export(
        scenario_dir("basic-inbox"),
        entry["reference_epoch"],
        entry["maxage_sec"],
        entry["tz_offset"],
    )
    assert doc["synced_messages"] == expect["synced_messages"]
    assert doc["synced_bytes"] == expect["synced_bytes"]
    assert doc["synced_bytes"] != doc["synced_messages"]


def test_tz_offset_changes_cutoff() -> None:
    """tz_offset minutes shift cutoff per maxage-window.md."""
    proc = sync_cli("tz-offset")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    doc = load_export("tz-offset")
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == "tz-offset")
    expect_cutoff = maxage_cutoff(
        entry["reference_epoch"], entry["maxage_sec"], entry["tz_offset"]
    )
    assert doc["cutoff_utc"] == expect_cutoff
    assert doc["synced_messages"] == 1


def test_dry_run_skips_sync_run_state() -> None:
    """Dry-run must not write sync-run.json."""
    proc = sync_cli("basic-inbox", dry_run=True, export_name="dry-basic.json")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert not SYNC_RUN_PATH.exists()
    doc = load_export("basic-inbox", export_name="dry-basic.json")
    assert doc["dry_run"] is True


def test_non_dry_run_writes_sync_run() -> None:
    """Real sync persists sync-run.json with full documented schema."""
    proc = sync_cli("basic-inbox")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert SYNC_RUN_PATH.exists()
    run_doc = json.loads(SYNC_RUN_PATH.read_text(encoding="utf-8"))
    export = load_export("basic-inbox")
    meta, _rules = scenario_meta("basic-inbox")
    validate_sync_run(run_doc, export, meta)


@pytest.mark.parametrize("scenario_name", [s["name"] for s in CATALOG["scenarios"]])
def test_sync_run_schema_matches_docs(scenario_name: str) -> None:
    """sync-run.json must satisfy export-summary.md schema version 1."""
    proc = sync_cli(scenario_name)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert SYNC_RUN_PATH.exists()
    run_doc = json.loads(SYNC_RUN_PATH.read_text(encoding="utf-8"))
    export = load_export(scenario_name)
    meta, _rules = scenario_meta(scenario_name)
    validate_sync_run(run_doc, export, meta)


def test_uidvalidity_reset_clears_high_uid() -> None:
    """UIDVALIDITY bump must reset ledger high_uid before re-sync."""
    import shutil
    import tempfile

    sdir = scenario_dir("basic-inbox")
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == "basic-inbox")
    proc1 = sync_cli("basic-inbox")
    assert proc1.returncode == 0, proc1.stderr or proc1.stdout
    high = sqlite3.connect(LEDGER_PATH).execute(
        "SELECT high_uid FROM folder_cache WHERE folder='INBOX'"
    ).fetchone()
    baseline_expect = simulate_sync_export(
        sdir, entry["reference_epoch"], entry["maxage_sec"], entry["tz_offset"]
    )
    assert high is not None and high[0] == baseline_expect["synced_messages"]

    work = Path(tempfile.mkdtemp(dir=OUTPUT))
    shutil.copytree(sdir, work / "basic-inbox", dirs_exist_ok=True)
    bumped = work / "basic-inbox" / "imap-meta.json"
    meta = json.loads(bumped.read_text(encoding="utf-8"))
    meta["folders"][0]["uidvalidity"] += 76
    bumped.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    proc2 = sync_cli(
        "basic-inbox",
        root=work,
        imap_meta=bumped,
        export_name="basic-bump.json",
    )
    assert proc2.returncode == 0, proc2.stderr or proc2.stdout
    row = sqlite3.connect(LEDGER_PATH).execute(
        "SELECT uidvalidity, high_uid FROM folder_cache WHERE folder='INBOX'"
    ).fetchone()
    expected_high = baseline_expect["synced_messages"]
    assert row == (meta["folders"][0]["uidvalidity"], expected_high)
    export = load_export("basic-inbox", export_name="basic-bump.json")
    expect = simulate_sync_export(
        work / "basic-inbox", entry["reference_epoch"], entry["maxage_sec"], entry["tz_offset"]
    )
    assert export == expect


def test_maxage_offset_env_tightens_window() -> None:
    """OI_MAXAGE_OFFSET_SEC probe shrinks eligible rows."""
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == "basic-inbox")
    base_rows = load_manifest(scenario_dir("basic-inbox") / "messages.tsv")
    cutoff_base = maxage_cutoff(entry["reference_epoch"], entry["maxage_sec"], entry["tz_offset"])
    base_selected = sorted(
        [row for row in base_rows if row.internal_date >= cutoff_base],
        key=lambda row: row.internal_date,
        reverse=True,
    )
    desired_cutoff = base_selected[1].internal_date + 1
    offset_seconds = desired_cutoff - cutoff_base
    env = {"OI_MAXAGE_OFFSET_SEC": str(offset_seconds)}
    proc = sync_cli("basic-inbox", env=env, export_name="offset.json")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    doc = load_export("basic-inbox", export_name="offset.json")
    os.environ["OI_MAXAGE_OFFSET_SEC"] = str(offset_seconds)
    try:
        expect = simulate_sync_export(
            scenario_dir("basic-inbox"),
            entry["reference_epoch"],
            entry["maxage_sec"],
            entry["tz_offset"],
        )
    finally:
        os.environ.pop("OI_MAXAGE_OFFSET_SEC", None)
    assert doc == expect
    assert doc["synced_messages"] == 1


def test_verifier_validity_bump_scenario() -> None:
    """Hidden validity-bump scenario under /opt/verifier-fixtures must match reference export."""
    entry, verifier_scenarios = verifier_scenario("uidvalidity-reset")
    export_name = f"{entry['name']}.json"
    proc = sync_cli(
        str(entry["name"]),
        root=verifier_scenarios,
        catalog={"scenarios": [entry]},
        export_name=export_name,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export("basic-inbox", export_name=export_name)
    expect = simulate_sync_export(
        verifier_scenarios / str(entry["name"]),
        entry["reference_epoch"],
        entry["maxage_sec"],
        entry["tz_offset"],
    )
    assert got == expect


def test_folder_filter_before_maxage_reference_rows() -> None:
    """Manifest ingest rows use folder gate before maxage cutoff."""
    scenario_name = scenario_name_with_rule("exclude Work/Archive")
    sdir = scenario_dir(scenario_name)
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == scenario_name)
    meta = json.loads((sdir / "imap-meta.json").read_text(encoding="utf-8"))
    rules = (sdir / "folder.rules").read_text(encoding="utf-8")
    rows = load_manifest(sdir / "messages.tsv")
    eligible = set(filter_folders([f["name"] for f in meta["folders"]], rules))
    cutoff = maxage_cutoff(entry["reference_epoch"], entry["maxage_sec"], entry["tz_offset"])
    selected = select_messages(rows, eligible, cutoff)
    expected = simulate_sync_export(
        sdir, entry["reference_epoch"], entry["maxage_sec"], entry["tz_offset"]
    )
    assert sum(r.size_bytes for r in selected) == expected["synced_bytes"]


def test_protected_files_unmodified() -> None:
    """Contract docs and bundled fixture data must remain unchanged."""
    for rel, digest in PROTECTED_SHA256.items():
        assert _sha256(rel) == digest, rel


def test_ledger_untouched_on_dry_run_after_real_sync() -> None:
    """Dry-run after a real sync must leave sync-ledger.db byte-for-byte unchanged."""
    scenario_name = scenario_name_with_rule("exclude Work/Archive")
    proc_real = sync_cli(scenario_name)
    assert proc_real.returncode == 0, proc_real.stderr or proc_real.stdout
    assert LEDGER_PATH.is_file()
    ledger_before = LEDGER_PATH.read_bytes()
    rows_before = ledger_rows()

    proc_dry = sync_cli(scenario_name, dry_run=True, export_name="dry-work.json")
    assert proc_dry.returncode == 0, proc_dry.stderr or proc_dry.stdout

    assert LEDGER_PATH.read_bytes() == ledger_before
    assert ledger_rows() == rows_before


def test_cli_requires_mailbox_paths() -> None:
    """Driver rejects incomplete invocation."""
    proc = run([CLI, "sync"])
    assert proc.returncode != 0


def test_repeat_sync_idempotent_export() -> None:
    """Second sync on unchanged inputs must yield the same export JSON."""
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == "basic-inbox")
    proc1 = sync_cli("basic-inbox", export_name="idem1.json")
    assert proc1.returncode == 0, proc1.stderr or proc1.stdout
    proc2 = sync_cli("basic-inbox", export_name="idem2.json")
    assert proc2.returncode == 0, proc2.stderr or proc2.stdout
    first = load_export("basic-inbox", export_name="idem1.json")
    second = load_export("basic-inbox", export_name="idem2.json")
    expect = simulate_sync_export(
        scenario_dir("basic-inbox"),
        entry["reference_epoch"],
        entry["maxage_sec"],
        entry["tz_offset"],
    )
    assert first == expect
    assert second == expect


def test_snapshot_marks_excluded_folders_unselected() -> None:
    """Excluded folders remain visible in snapshot with selected=false."""
    scenario_name = scenario_name_with_rule("exclude Work/Archive")
    proc = sync_cli(scenario_name)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    snap = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    by_name = {f["name"]: f["selected"] for f in snap["folders"]}
    assert by_name["Work/Archive"] is False
    assert by_name["Work/Active"] is True
    assert by_name["INBOX"] is True


def test_export_folders_sorted() -> None:
    """Export folders list must be sorted ascending."""
    scenario_name = scenario_name_with_rule("exclude Work/Archive")
    proc = sync_cli(scenario_name)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    doc = load_export(scenario_name)
    assert doc["folders"] == sorted(doc["folders"])


def test_sync_run_dry_run_false_on_real_sync() -> None:
    """sync-run.json from a real sync must record dry_run=false."""
    proc = sync_cli("basic-inbox")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    run_doc = json.loads(SYNC_RUN_PATH.read_text(encoding="utf-8"))
    export = load_export("basic-inbox")
    meta, _rules = scenario_meta("basic-inbox")
    validate_sync_run(run_doc, export, meta)


def test_verifier_exclude_only_rules_scenario() -> None:
    """Hidden exclude-only rules under /opt/verifier-fixtures must match reference."""
    entry, verifier_scenarios = verifier_scenario("exclude-filter-only")
    export_name = f"{entry['name']}.json"
    proc = sync_cli(
        str(entry["name"]),
        root=verifier_scenarios,
        catalog={"scenarios": [entry]},
        export_name=export_name,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_export("basic-inbox", export_name=export_name)
    expect = simulate_sync_export(
        verifier_scenarios / str(entry["name"]),
        entry["reference_epoch"],
        entry["maxage_sec"],
        entry["tz_offset"],
    )
    assert got == expect


def test_contract_state_and_output_paths_after_sync() -> None:
    """Real sync must write /app/output/basic-inbox.json, /app/state/folder-snapshot.json, /app/state/sync-ledger.db, and /app/state/sync-run.json."""
    proc = sync_cli("basic-inbox")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert Path("/app/output").is_dir()
    assert Path("/app/output/basic-inbox.json").is_file()
    assert Path("/app/state/folder-snapshot.json").is_file()
    assert Path("/app/state/sync-ledger.db").is_file()
    assert Path("/app/state/sync-run.json").is_file()


def test_ledger_high_uid_tracks_max_selected_uid() -> None:
    """Ledger high_uid must reflect the maximum uid among selected messages."""
    scenario_name = scenario_name_with_rule("exclude Work/Archive")
    proc = sync_cli(scenario_name)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    rows = sqlite3.connect(LEDGER_PATH).execute(
        "SELECT folder, high_uid FROM folder_cache ORDER BY folder"
    ).fetchall()
    entry = next(s for s in CATALOG["scenarios"] if s["name"] == scenario_name)
    expected = simulate_sync_export(
        scenario_dir(scenario_name),
        entry["reference_epoch"],
        entry["maxage_sec"],
        entry["tz_offset"],
    )
    expected_highs = {
        folder: max(row.uid for row in select_messages(
            load_manifest(scenario_dir(scenario_name) / "messages.tsv"),
            set(expected["folders"]),
            expected["cutoff_utc"],
        ) if row.folder == folder)
        for folder in expected["folders"]
    }
    assert ("INBOX", expected_highs["INBOX"]) in rows
    assert ("Work/Active", expected_highs["Work/Active"]) in rows
    assert all(folder != "Work/Archive" for folder, _ in rows)
