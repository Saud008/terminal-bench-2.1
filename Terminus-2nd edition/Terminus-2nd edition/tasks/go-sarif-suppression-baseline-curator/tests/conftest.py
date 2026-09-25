"""Pytest fixtures for sarbctl verifier runs."""

from __future__ import annotations

import subprocess

import pytest

from sarbctl_runner import (
    APP,
    BASELINE,
    CLI,
    POLICY,
    REMAP,
    SARIF,
    wipe_state,
)


@pytest.fixture(scope="session", autouse=True)
def rebuild_sarbctl_binary() -> None:
    rebuild = APP / "scripts" / "verifier-rebuild.sh"
    proc = subprocess.run(["bash", str(rebuild)], check=False)
    assert proc.returncode == 0, proc.stderr if hasattr(proc, "stderr") else proc
    proc = subprocess.run(
        [
            "go",
            "build",
            "-mod=readonly",
            "-trimpath",
            "-ldflags=-s -w",
            "-o",
            str(CLI),
            "./cmd/sarbctl",
        ],
        cwd=str(APP),
        check=False,
    )
    assert proc.returncode == 0


@pytest.fixture()
def clean_workspace() -> None:
    wipe_state()


@pytest.fixture()
def bundled_paths() -> dict[str, str]:
    return {
        "sarif": str(SARIF),
        "policy": str(POLICY),
        "remap": str(REMAP),
        "baseline": str(BASELINE),
    }
