import hashlib
import json
from pathlib import Path

import offlineimap_contracts as _contracts
from offlineimap_cutoff import maxage_cutoff
from offlineimap_export_model import export_summary, select_messages
import offlineimap_hidden_cases as _hidden_cases
import offlineimap_integrity as _integrity
import offlineimap_ledger as _ledger
from offlineimap_manifest import load_manifest
import offlineimap_manifest as _manifest
import offlineimap_paths as _paths
import offlineimap_rules as _rules
from offlineimap_snapshot import build_snapshot
import offlineimap_snapshot as _snapshot

FOLDER_ENTRY_KEYS = _contracts.FOLDER_ENTRY_KEYS
FOLDER_SNAPSHOT_KEYS = _contracts.FOLDER_SNAPSHOT_KEYS
SYNC_RUN_KEYS = _contracts.SYNC_RUN_KEYS
HIDDEN_CASE_KINDS = _hidden_cases.HIDDEN_CASE_KINDS
PROTECTED_SHA256 = _integrity.PROTECTED_SHA256
ledger_prepare = _ledger.ledger_prepare
ledger_update_high = _ledger.ledger_update_high
ManifestRow = _manifest.ManifestRow
APP = _paths.APP
LEDGER_PATH = _paths.LEDGER_PATH
SNAPSHOT_PATH = _paths.SNAPSHOT_PATH
SYNC_RUN_PATH = _paths.SYNC_RUN_PATH
filter_folders = _rules.filter_folders
folder_matches = _rules.folder_matches
parse_rules = _rules.parse_rules
folder_digest = _snapshot.folder_digest


def simulate_sync_export(
    scenario_dir: Path,
    reference_epoch: int,
    maxage_sec: int,
    tz_offset: int,
    *,
    dry_run: bool = False,
) -> dict:
    meta = json.loads((scenario_dir / "imap-meta.json").read_text(encoding="utf-8"))
    rules_text = (scenario_dir / "folder.rules").read_text(encoding="utf-8")
    rows = load_manifest(scenario_dir / "messages.tsv")
    snapshot = build_snapshot(meta, rules_text)
    eligible = {folder["name"] for folder in snapshot["folders"] if folder["selected"]}
    cutoff = maxage_cutoff(reference_epoch, maxage_sec, tz_offset)
    selected = select_messages(rows, eligible, cutoff)
    return export_summary(
        meta, selected, reference_epoch, maxage_sec, tz_offset, dry_run, cutoff
    )


def simulate_snapshot(scenario_dir: Path) -> dict:
    meta = json.loads((scenario_dir / "imap-meta.json").read_text(encoding="utf-8"))
    rules_text = (scenario_dir / "folder.rules").read_text(encoding="utf-8")
    return build_snapshot(meta, rules_text)


def validate_folder_snapshot(doc: dict, meta: dict, rules_text: str) -> None:
    assert set(doc.keys()) == FOLDER_SNAPSHOT_KEYS
    assert doc["schema"] == 1
    assert doc["account"] == meta["account"]
    folders = doc["folders"]
    assert isinstance(folders, list)
    assert len(folders) == len(meta["folders"])
    expected = build_snapshot(meta, rules_text)
    assert doc["folder_digest"] == expected["folder_digest"]
    for idx, (got, exp, meta_folder) in enumerate(
        zip(folders, expected["folders"], meta["folders"], strict=True)
    ):
        assert set(got.keys()) == FOLDER_ENTRY_KEYS, idx
        assert got["name"] == meta_folder["name"] == exp["name"], idx
        assert got["uidvalidity"] == meta_folder["uidvalidity"] == exp["uidvalidity"], idx
        assert got["selected"] is exp["selected"], idx
        assert isinstance(got["selected"], bool), idx


def validate_sync_run(doc: dict, export_doc: dict, meta: dict) -> None:
    assert set(doc.keys()) == SYNC_RUN_KEYS
    assert doc["schema"] == 1
    assert doc["account"] == meta["account"]
    assert doc["reference_epoch"] == export_doc["reference_epoch"]
    assert doc["synced_messages"] == export_doc["synced_messages"]
    assert doc["synced_bytes"] == export_doc["synced_bytes"]
    assert doc["dry_run"] is False


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
