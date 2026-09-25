"""G-026 primary pytest module — kiln heat balance ledger verifier entrypoint."""

import subprocess

from kiln_balance_verifier import reference_heat_balance, reference_probe_timeline
from test_heat_ledger import *  # noqa: F403
from test_probe_buffer import *  # noqa: F403


def test_subprocess_kilnbal_help_invocation():
    """Primary test_outputs subprocess smoke ensures kilnbal CLI is invoked outside helper imports."""
    proc = subprocess.run(
        ["/app/bin/kilnbal"],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0


def test_verifier_helpers_importable_from_outputs_entry():
    """test_outputs.py exposes kiln_balance_verifier helpers for unacceptable-class SYNTHETIC gate."""
    assert callable(reference_heat_balance)
    assert callable(reference_probe_timeline)
