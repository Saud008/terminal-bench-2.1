"""Hydrate ingest, residual-matrix buffer snapshots, and seal-closure certificate export tests."""

from __future__ import annotations

import json

from closure_spec import reference_certificate
from plate_session import FIXTURES, WORK, cert, reset, run, run_full


def test_residual_matrix_buffer_header() -> None:
    """bind-residuals must write a residual-matrix buffer with a typed header line."""
    reset()
    assert run("hydrate-plates", "plate-tight-tan").returncode == 0
    assert run("bind-residuals", "plate-tight-tan").returncode == 0
    path = WORK / "residual-matrix" / "plate-tight-tan.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])
    assert header == {"type": "residual-matrix", "scenario_id": "plate-tight-tan"}


def test_hydrate_primes_laboratory_journal() -> None:
    """hydrate-plates must run before bind-residuals without error."""
    reset()
    proc = run("hydrate-plates", "plate-multi-star")
    assert proc.returncode == 0
    assert proc.stderr == ""


def test_bind_before_seal_certificate() -> None:
    """bind-residuals must complete before seal-closure writes the certificate."""
    reset()
    assert run("bind-residuals", "plate-repeat-seal").returncode == 0
    assert (WORK / "residual-matrix" / "plate-repeat-seal.jsonl").exists()
    assert run("seal-closure", "plate-repeat-seal").returncode == 0
    assert cert("plate-repeat-seal")["scenario_id"] == "plate-repeat-seal"


def test_certificate_default_filename() -> None:
    """seal-closure must default to scenario-closure-certificate.json under /app/output/."""
    reset()
    run_full("plate-tight-tan")
    body = cert("plate-tight-tan")
    assert body == reference_certificate(FIXTURES / "plate-tight-tan.json")


def test_matrix_rows_sorted_by_star_id() -> None:
    """matrix buffer rows must remain sorted by star_id ascending."""
    reset()
    run_full("plate-multi-star")
    lines = (WORK / "residual-matrix" / "plate-multi-star.jsonl").read_text(encoding="utf-8").splitlines()[1:]
    ids = [json.loads(line)["star_id"] for line in lines]
    assert ids == sorted(ids)


def test_seal_repeat_byte_identical() -> None:
    """repeat seal-closure must not mutate certificate bytes."""
    reset()
    run_full("plate-repeat-seal")
    first = cert("plate-repeat-seal")
    assert run("seal-closure", "plate-repeat-seal").returncode == 0
    assert cert("plate-repeat-seal") == first


def test_hidden_matrix_certificate_under_tb3_fixture_dir() -> None:
    """TB3 fixture overlay must still produce matrix buffer and certificate."""
    reset()
    env = {"TB3_FIXTURE_DIR": "/opt/verifier-fixtures/platclosectl/scenarios"}
    run_full("hidden-cat-mask-bit", env=env)
    assert cert("hidden-cat-mask-bit")["stars"] == ["S01"]
