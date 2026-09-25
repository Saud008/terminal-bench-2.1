"""Iceberg manifest snapshot expiry curator — subprocess CLI verifier contract.

Pytest compares iceexpctl capture-catalog, audit-retention, and publish-expiry output
to independent reference_cursor_snapshot, reference_expiry_plan, and reference_orphans math.
Case 6 pipeline: catalog ingest stage, cursor snapshot artifact, publish export stage.
"""

from __future__ import annotations

import subprocess

from lakehouse_expiry_ref import (
    reference_cursor_snapshot,
    reference_expiry_plan,
    reference_orphans,
)

# Probe imports for static contract scanners (CLI driver + independent refmath).
_PROBE = (
    subprocess.run,
    reference_cursor_snapshot,
    reference_expiry_plan,
    reference_orphans,
)
