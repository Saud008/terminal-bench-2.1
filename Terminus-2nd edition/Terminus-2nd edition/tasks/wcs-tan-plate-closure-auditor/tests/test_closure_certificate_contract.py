"""Certificate digest, seal gating, and repeat-seal stability contracts."""

from __future__ import annotations

from closure_spec import closure_digest, reference_certificate
from plate_session import FIXTURES, OUTPUT, cert, reset, run, run_full


def test_seal_requires_prior_bind_pass() -> None:
    """seal-closure without bind_pass must fail and must not write output."""
    reset()
    out = OUTPUT / "plate-repeat-seal-closure-certificate.json"
    if out.exists():
        out.unlink()
    proc = run("seal-closure", "plate-repeat-seal")
    assert proc.returncode != 0
    assert not out.exists()


def test_digest_matches_normative_bytes() -> None:
    """closure_digest must match the six-decimal normative payload in docs."""
    reset()
    run_full("plate-tight-tan")
    body = cert("plate-tight-tan")
    assert body["closure_digest"] == closure_digest(
        body["scenario_id"], body["stars"], body["rms_ra_arcsec"], body["rms_dec_arcsec"]
    )
    assert body == reference_certificate(FIXTURES / "plate-tight-tan.json")


def test_repeat_seal_is_byte_identical() -> None:
    """Repeated seal-closure must not change certificate bytes."""
    reset()
    run_full("plate-repeat-seal")
    first = (OUTPUT / "plate-repeat-seal-closure-certificate.json").read_bytes()
    assert run("seal-closure", "plate-repeat-seal").returncode == 0
    second = (OUTPUT / "plate-repeat-seal-closure-certificate.json").read_bytes()
    assert first == second
