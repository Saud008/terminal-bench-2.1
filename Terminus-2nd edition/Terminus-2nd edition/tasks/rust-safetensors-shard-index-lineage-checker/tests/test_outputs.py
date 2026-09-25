"""Pytest entrypoint for the safetensors shard index contract suite."""
from __future__ import annotations

from pathlib import Path

from xr7_ref_harness import catalog_dir, load_journal_rows, pipeline, rebuild, weight_root
from xr7_ref_math import reference_journal
from test_xr7_contract import *  # noqa: F401,F403


def reference_shard_journal(catalogs=None, weights=None):
    """Independent reference helper exposed from the verifier entrypoint."""
    from pathlib import Path

    c = Path(catalogs) if catalogs else catalog_dir()
    w = Path(weights) if weights else weight_root()
    return reference_journal(c, w)


def test_reference_helper_smoke_row_count():
    """The verifier entrypoint must expose an independent reference helper."""
    rebuild()
    pipeline()
    got = load_journal_rows()
    ref = reference_shard_journal()
    assert len(got) == len(ref)


def test_entrypoint_writes_lineage_report_path():
    """The verifier entrypoint must assert that /app/lineage/weight_lineage_atlas.json is written."""
    rebuild()
    pipeline()
    assert Path("/app/lineage/weight_lineage_atlas.json").is_file()


def test_entrypoint_writes_shard_journal_path():
    """The verifier entrypoint must assert that /app/var/xr7_journal.ndjson is written."""
    rebuild()
    pipeline()
    assert Path("/app/var/xr7_journal.ndjson").is_file()
