"""Vault snapshot contract tests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from dossier_harness import (
    CLI_BIN,
    SEED_POOL,
    SNAP_PATH,
    TRUSTED_ARCHIVE_DIR,
    invoke,
    load_json_nofollow,
    reset_workspace,
)
from dossier_lineage_math import materialize_archive


@pytest.fixture(autouse=True)
def isolate_workspace():
    reset_workspace()
    yield
    reset_workspace()


def test_vault_json_includes_focus_accession_id():
    """Vault snapshot focus_accession_id must resolve from the archive focus ref for the seed."""
    seed = SEED_POOL[2]
    proc = invoke([str(CLI_BIN), "vault", "load", "--seed", seed, "--archive", "rights-precedence"])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    snap = load_json_nofollow(SNAP_PATH)
    arch = materialize_archive(TRUSTED_ARCHIVE_DIR / "rights-precedence.json", seed)
    assert snap["focus_accession_id"] == arch["_focus"]


def test_archive_seq_bumps_on_repeated_vault_load():
    """Repeated vault load for the same seed must bump archive_seq on the snapshot."""
    seed = SEED_POOL[0]
    for _ in range(2):
        proc = invoke([str(CLI_BIN), "vault", "load", "--seed", seed, "--archive", "basic-custody"])
        assert proc.returncode == 0, proc.stderr + proc.stdout
    snap = load_json_nofollow(SNAP_PATH)
    assert snap["archive_seq"] == 2


def test_archive_seq_bumps_across_seed_and_archive_changes():
    """archive_seq belongs to the snapshot path, not a seed/archive pair."""
    first = invoke(
        [str(CLI_BIN), "vault", "load", "--seed", SEED_POOL[0], "--archive", "basic-custody"]
    )
    assert first.returncode == 0, first.stderr + first.stdout
    second = invoke(
        [str(CLI_BIN), "vault", "load", "--seed", SEED_POOL[1], "--archive", "loan-overlap"]
    )
    assert second.returncode == 0, second.stderr + second.stdout
    snap = load_json_nofollow(SNAP_PATH)
    assert snap["archive_seq"] == 2


def test_mismatched_embedded_archive_name_is_rejected_without_replacement():
    """Selected filename and embedded archive_name must agree."""
    original = b'{"archive_seq":41,"seed":"sentinel"}\n'
    SNAP_PATH.write_bytes(original)
    with tempfile.TemporaryDirectory() as tmp:
        overlay = Path(tmp)
        payload = json.loads(
            (TRUSTED_ARCHIVE_DIR / "basic-custody.json").read_text(encoding="utf-8")
        )
        payload["archive_name"] = "different-name"
        (overlay / "claimed-name.json").write_text(json.dumps(payload), encoding="utf-8")
        proc = invoke(
            [str(CLI_BIN), "vault", "load", "--seed", SEED_POOL[0], "--archive", "claimed-name"],
            env={"TB3_ARCHIVE_DIR": str(overlay)},
        )
    assert proc.returncode != 0
    assert SNAP_PATH.read_bytes() == original


def test_corrupt_existing_snapshot_blocks_sequence_reset():
    """A corrupt prior snapshot cannot be silently replaced with archive_seq one."""
    original = b'{"archive_seq":'
    SNAP_PATH.write_bytes(original)
    proc = invoke(
        [str(CLI_BIN), "vault", "load", "--seed", SEED_POOL[0], "--archive", "basic-custody"]
    )
    assert proc.returncode != 0
    assert SNAP_PATH.read_bytes() == original


def test_vault_preserves_museum_id_and_as_of_date():
    """Vault load must preserve museum_id and as_of_date from the selected archive."""
    seed = SEED_POOL[1]
    proc = invoke([str(CLI_BIN), "vault", "load", "--seed", seed, "--archive", "loan-overlap"])
    assert proc.returncode == 0
    snap = load_json_nofollow(SNAP_PATH)
    assert snap["museum_id"] == "MUS-NAT-01"
    assert snap["as_of_date"] == "2024-08-01"
