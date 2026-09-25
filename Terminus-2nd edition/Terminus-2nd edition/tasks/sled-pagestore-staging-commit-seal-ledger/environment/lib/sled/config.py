from __future__ import annotations

from pathlib import Path

APP = Path("/app")
STATE = APP / "state"
COMMITTED_PATH = STATE / "committed.json"
STAGING_PATH = STATE / "staging.json"
REGISTRY_PATH = STATE / "page_registry.json"
JOURNAL_PATH = STATE / "split_journal.jsonl"
SNAPSHOT_PATH = STATE / "sled-staging-snapshot.json"
COMMIT_RECORD_PATH = STATE / "commit_record.json"
PAGES_PATH = STATE / "pages.json"
APPLIED_PATH = STATE / "applied_splits.json"
PINS_DIR = STATE / "pins"
OUTPUT = APP / "output"

ORDER = 4
