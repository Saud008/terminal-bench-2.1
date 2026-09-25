"""Shared JSON loaders for vaultaud verifier suites."""
from __future__ import annotations

import json

from vaultaud_cli import ATLAS, LEDGER


def read_staging_rows() -> list[dict]:
    rows = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def read_atlas_doc() -> dict:
    return json.loads(ATLAS.read_text(encoding="utf-8"))
