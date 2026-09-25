"""G-026 primary pytest module — rotrace fouling chronicle smoke entrypoint."""

from __future__ import annotations

import subprocess


def test_subprocess_rotrace_help_invocation():
    """Primary test_outputs subprocess smoke ensures rotrace CLI is invoked outside helper imports."""
    proc = subprocess.run(
        ["/app/bin/rotrace"],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0


def test_fouling_reference_chronicle_callable():
    """test_outputs.py exposes reference_chronicle helpers for unacceptable-class SYNTHETIC gate."""
    from brine_ndp_contract import reference_chronicle

    assert callable(reference_chronicle)


def test_swro_pipeline_driver_importable():
    """Smoke import ensures swro_pipeline_driver subprocess helpers are loadable."""
    from swro_pipeline_driver import run_swro_fouling_pipeline  # noqa: F401
