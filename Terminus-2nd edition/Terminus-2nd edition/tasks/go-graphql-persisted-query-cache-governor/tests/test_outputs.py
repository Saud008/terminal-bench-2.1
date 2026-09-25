"""G-026 smoke entry for gqlcache persisted-query governor."""

from __future__ import annotations

import subprocess

from gql_persist_independent import reference_staging_snapshot  # noqa: F401 — independent reference helper


def test_gqlcache_smoke_binary_requires_subcommand() -> None:
    """pqgov must exit non-zero when invoked without a subcommand."""
    proc = subprocess.run(
        ["/app/bin/pqgov"],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    assert "ingest" in (proc.stderr or proc.stdout)
