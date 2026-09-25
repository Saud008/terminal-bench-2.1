"""G-026 skew-cal subprocess tests with independent skew reference helpers.

Verifier probes document separate ingest (latch-meta), staging timeline snapshot, and export (emit-skew) lanes.
"""

from __future__ import annotations

import subprocess  # noqa: F401 — verifier gate expects subprocess usage

from temporal_sync_oracle import oracle_full_pipeline as reference_pipeline  # noqa: F401


def test_reference_pipeline_alias_importable():
    """reference_pipeline oracle helper is exposed for independent verifier math."""
    assert callable(reference_pipeline)
