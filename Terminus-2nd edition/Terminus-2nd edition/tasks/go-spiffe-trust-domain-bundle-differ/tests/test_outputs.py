"""SPIFFE trust-domain bundle differ — subprocess CLI ingest bind and atlas export pipeline.

Verifier contract uses pair capture staging snapshot digests and federation atlas emission.
Independent reference math lives in identity_bundle_ref.
"""

from __future__ import annotations

import json
import os
import subprocess

import pytest
from identity_bundle_ref import (
    expected_federation_atlas,
    expected_pair_capture,
    order_jwks_keys,
    rot_window,
)
from spiffectl_runner import (
    FIXTURE_SCENARIOS,
    SPIFFE_ATLAS,
    SPIFFE_BIN,
    SPIFFE_CAPTURE,
    SPIFFE_FIXTURES,
    SPIFFE_HIDDEN,
    SPIFFE_LEFT,
    SPIFFE_SEAL,
    read_json,
    reset_spiffe_workspace,
    run_spiffe_cli,
    run_spiffe_pipeline,
)


def test_spiffe_smoke_bind_writes_pair_capture_path() -> None:
    """Verify smoke bind writes pair capture path."""
    reset_spiffe_workspace()
    proc = run_spiffe_cli(
        [SPIFFE_BIN, "bind-pair", "--scenario", "trust-domain-hostfold", "--fixture-dir", str(SPIFFE_FIXTURES)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert SPIFFE_CAPTURE.is_file()


def test_spiffe_smoke_staging_left_matches_fixture_after_bind() -> None:
    """Verify smoke staging left matches fixture after bind."""
    reset_spiffe_workspace()
    run_spiffe_cli([SPIFFE_BIN, "bind-pair", "--scenario", "stable-diff-pair", "--fixture-dir", str(SPIFFE_FIXTURES)])
    body = json.loads(SPIFFE_CAPTURE.read_text(encoding="utf-8"))
    left_fixture = json.loads((SPIFFE_FIXTURES / "scenarios/stable-diff-pair/left.json").read_text(encoding="utf-8"))
    assert body["left"]["x509_svid"] == left_fixture["x509_svid"]


@pytest.mark.parametrize("scenario_id", FIXTURE_SCENARIOS)
def test_spiffe_ibv01_pair_capture_digest_matches_refmath(scenario_id: str) -> None:
    """Verify ibv01 pair capture digest matches refmath."""
    reset_spiffe_workspace()
    proc = run_spiffe_cli(
        [SPIFFE_BIN, "bind-pair", "--scenario", scenario_id, "--fixture-dir", str(SPIFFE_FIXTURES)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(SPIFFE_CAPTURE.read_text(encoding="utf-8"))
    ref = expected_pair_capture(scenario_id, SPIFFE_FIXTURES)
    assert body["capture_digest"] == ref["capture_digest"]


def test_spiffe_ibv02_trust_domain_lowercased_after_normalize_trust() -> None:
    """Verify ibv02 trust domain lowercased after normalize trust."""
    reset_spiffe_workspace()
    run_spiffe_cli([SPIFFE_BIN, "bind-pair", "--scenario", "trust-domain-hostfold", "--fixture-dir", str(SPIFFE_FIXTURES)])
    run_spiffe_cli([SPIFFE_BIN, "normalize-trust", "--scenario", "trust-domain-hostfold"])
    left = json.loads(SPIFFE_LEFT.read_text(encoding="utf-8"))
    assert left["trust_domain"] == "mixed.case.org"


def test_spiffe_ibv03_jwks_sig_before_enc() -> None:
    """Verify ibv03 jwks sig before enc."""
    reset_spiffe_workspace()
    run_spiffe_cli([SPIFFE_BIN, "bind-pair", "--scenario", "jwks-key-order", "--fixture-dir", str(SPIFFE_FIXTURES)])
    run_spiffe_cli([SPIFFE_BIN, "normalize-trust", "--scenario", "jwks-key-order"])
    left = json.loads(SPIFFE_LEFT.read_text(encoding="utf-8"))
    uses = [k["use"] for k in left["jwks"]["keys"]]
    assert uses.index("sig") < uses.index("enc")


def test_spiffe_ibv04_x509_serial_strips_leading_zeros() -> None:
    """Verify ibv04 x509 serial strips leading zeros."""
    reset_spiffe_workspace()
    run_spiffe_cli([SPIFFE_BIN, "bind-pair", "--scenario", "x509-serial-normalize", "--fixture-dir", str(SPIFFE_FIXTURES)])
    run_spiffe_cli([SPIFFE_BIN, "normalize-trust", "--scenario", "x509-serial-normalize"])
    left = json.loads(SPIFFE_LEFT.read_text(encoding="utf-8"))
    assert left["x509_svid"][0]["serial"] == "abc0"


def test_spiffe_ibv05_rotation_window_keeps_inclusive_bounds() -> None:
    """Verify ibv05 rotation window keeps inclusive bounds."""
    reset_spiffe_workspace()
    run_spiffe_cli([SPIFFE_BIN, "bind-pair", "--scenario", "rotation-window", "--fixture-dir", str(SPIFFE_FIXTURES)])
    run_spiffe_cli([SPIFFE_BIN, "normalize-trust", "--scenario", "rotation-window"])
    left = json.loads(SPIFFE_LEFT.read_text(encoding="utf-8"))
    ids = {s["spiffe_id"] for s in left["x509_svid"]}
    assert "spiffe://example.org/w/in" in ids
    assert "spiffe://example.org/w/edge" in ids


def test_spiffe_ibv06_federation_wildcard_keeps_matching_allowlist() -> None:
    """Verify ibv06 federation wildcard keeps matching allowlist."""
    reset_spiffe_workspace()
    run_spiffe_cli([SPIFFE_BIN, "bind-pair", "--scenario", "federation-allowlist", "--fixture-dir", str(SPIFFE_FIXTURES)])
    run_spiffe_cli([SPIFFE_BIN, "normalize-trust", "--scenario", "federation-allowlist"])
    left = json.loads(SPIFFE_LEFT.read_text(encoding="utf-8"))
    assert "*.example.org" in left["federation_allowlist"]


def test_spiffe_ibv07_stale_identity_drops_old_last_seen() -> None:
    """Verify ibv07 stale identity drops old last seen."""
    reset_spiffe_workspace()
    run_spiffe_cli([SPIFFE_BIN, "bind-pair", "--scenario", "stale-identity", "--fixture-dir", str(SPIFFE_FIXTURES)])
    run_spiffe_cli([SPIFFE_BIN, "normalize-trust", "--scenario", "stale-identity"])
    left = json.loads(SPIFFE_LEFT.read_text(encoding="utf-8"))
    ids = {s["spiffe_id"] for s in left["x509_svid"]}
    assert "spiffe://example.org/workload/fresh" in ids
    assert "spiffe://example.org/workload/stale" not in ids


def test_spiffe_ibv08_normalize_trust_increments_seal_counter() -> None:
    """Verify ibv08 normalize trust increments seal counter."""
    reset_spiffe_workspace()
    run_spiffe_cli([SPIFFE_BIN, "bind-pair", "--scenario", "repeat-atlas", "--fixture-dir", str(SPIFFE_FIXTURES)])
    run_spiffe_cli([SPIFFE_BIN, "normalize-trust", "--scenario", "repeat-atlas"])
    gen = json.loads(SPIFFE_SEAL.read_text(encoding="utf-8"))
    assert gen["seal_counter"] >= 1


def test_spiffe_ibv09_refmath_jwks_order_sig_kid_lex() -> None:
    """Verify ibv09 refmath jwks order sig kid lex."""
    keys = [
        {"kid": "z-enc", "use": "enc"},
        {"kid": "m-sig", "use": "sig"},
        {"kid": "a-sig", "use": "sig"},
    ]
    ordered = order_jwks_keys(keys)
    assert [k["kid"] for k in ordered] == ["a-sig", "m-sig", "z-enc"]


@pytest.mark.parametrize(
    "scenario_id",
    ("stable-diff-pair", "federation-allowlist", "trust-domain-hostfold", "repeat-atlas"),
)
def test_spiffe_ibv10_atlas_report_matches_refmath(scenario_id: str) -> None:
    """Verify ibv10 atlas report matches refmath."""
    reset_spiffe_workspace()
    run_spiffe_pipeline(scenario_id)
    body = read_json(SPIFFE_ATLAS)
    ref = expected_federation_atlas(scenario_id, SPIFFE_FIXTURES)
    assert body["changes"] == ref["changes"]
    assert body["report_digest"] == ref["report_digest"]


def test_spiffe_ibv11_emit_atlas_blocked_before_normalize_trust() -> None:
    """Verify ibv11 emit atlas blocked before normalize trust."""
    reset_spiffe_workspace()
    run_spiffe_cli([SPIFFE_BIN, "bind-pair", "--scenario", "stable-diff-pair", "--fixture-dir", str(SPIFFE_FIXTURES)])
    proc = run_spiffe_cli([SPIFFE_BIN, "emit-atlas", "--scenario", "stable-diff-pair"])
    assert proc.returncode != 0


def test_spiffe_ibv12_repeatable_atlas_bytes_on_second_pass() -> None:
    """Verify ibv12 repeatable atlas bytes on second pass."""
    reset_spiffe_workspace()
    run_spiffe_pipeline("repeat-atlas")
    first = SPIFFE_ATLAS.read_bytes()
    proc = run_spiffe_cli([SPIFFE_BIN, "emit-atlas", "--scenario", "repeat-atlas"])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert SPIFFE_ATLAS.read_bytes() == first


def test_spiffe_ibv13_atlas_changes_sorted_by_path_ascending() -> None:
    """Verify ibv13 atlas changes sorted by path ascending."""
    reset_spiffe_workspace()
    run_spiffe_pipeline("stable-diff-pair")
    report = read_json(SPIFFE_ATLAS)
    paths = [c["path"] for c in report["changes"]]
    assert paths == sorted(paths)


def test_spiffe_ibv14_stable_diff_pair_reports_workload_delta() -> None:
    """Verify ibv14 stable diff pair reports workload delta."""
    reset_spiffe_workspace()
    run_spiffe_pipeline("stable-diff-pair")
    report = read_json(SPIFFE_ATLAS)
    paths = [c["path"] for c in report["changes"]]
    assert any("/workload/b" in p or "/workload/c" in p for p in paths)


def test_spiffe_ibv15_subprocess_cli_invokes_spiffectl_binary() -> None:
    """Verify ibv15 subprocess cli invokes spiffectl binary."""
    reset_spiffe_workspace()
    proc = subprocess.run([SPIFFE_BIN, "bind-pair"], capture_output=True, text=True, check=False)
    assert proc.returncode != 0


def test_spiffe_ibv16_normalize_trust_writes_normalized_left_file() -> None:
    """Verify ibv16 normalize trust writes normalized left file."""
    reset_spiffe_workspace()
    run_spiffe_cli([SPIFFE_BIN, "bind-pair", "--scenario", "jwks-key-order", "--fixture-dir", str(SPIFFE_FIXTURES)])
    run_spiffe_cli([SPIFFE_BIN, "normalize-trust", "--scenario", "jwks-key-order"])
    assert SPIFFE_LEFT.is_file()


def test_spiffe_ibv17_staging_left_matches_fixture_after_bind() -> None:
    """Verify ibv17 staging left matches fixture after bind."""
    reset_spiffe_workspace()
    run_spiffe_cli([SPIFFE_BIN, "bind-pair", "--scenario", "x509-serial-normalize", "--fixture-dir", str(SPIFFE_FIXTURES)])
    body = json.loads(SPIFFE_CAPTURE.read_text(encoding="utf-8"))
    ref = expected_pair_capture("x509-serial-normalize", SPIFFE_FIXTURES)
    assert body["left"] == ref["left"]


def test_spiffe_ibv18_repeatable_export_zero_changes() -> None:
    """Verify ibv18 repeatable export zero changes."""
    reset_spiffe_workspace()
    run_spiffe_pipeline("repeat-atlas")
    report = read_json(SPIFFE_ATLAS)
    assert report["change_count"] == 0


def test_spiffe_ibv19_tb3_federation_wildcard_hidden_fixture() -> None:
    """Verify ibv19 tb3 federation wildcard hidden fixture."""
    reset_spiffe_workspace()
    env = {"TB3_FIXTURE_DIR": str(SPIFFE_HIDDEN)}
    run_spiffe_cli(
        [SPIFFE_BIN, "bind-pair", "--scenario", "federation-wildcard-trap", "--fixture-dir", str(SPIFFE_HIDDEN)],
        env=env,
    )
    run_spiffe_cli([SPIFFE_BIN, "normalize-trust", "--scenario", "federation-wildcard-trap"], env=env)
    run_spiffe_cli([SPIFFE_BIN, "emit-atlas", "--scenario", "federation-wildcard-trap"], env=env)
    body = read_json(SPIFFE_ATLAS)
    ref = expected_federation_atlas("federation-wildcard-trap", SPIFFE_HIDDEN)
    assert body["changes"] == ref["changes"]


def test_spiffe_ibv20_tb3_rotation_boundary_hidden_fixture_window() -> None:
    """Verify ibv20 tb3 rotation boundary hidden fixture window."""
    reset_spiffe_workspace()
    env = {"TB3_FIXTURE_DIR": str(SPIFFE_HIDDEN), "TB3_ROT_WINDOW": "5"}
    run_spiffe_cli(
        [SPIFFE_BIN, "bind-pair", "--scenario", "rotation-boundary-trap", "--fixture-dir", str(SPIFFE_HIDDEN)],
        env=env,
    )
    run_spiffe_cli([SPIFFE_BIN, "normalize-trust", "--scenario", "rotation-boundary-trap"], env=env)
    prev = os.environ.get("TB3_ROT_WINDOW")
    os.environ["TB3_ROT_WINDOW"] = "5"
    try:
        ref = expected_federation_atlas("rotation-boundary-trap", SPIFFE_HIDDEN)
        assert rot_window() == 5
    finally:
        if prev is None:
            os.environ.pop("TB3_ROT_WINDOW", None)
        else:
            os.environ["TB3_ROT_WINDOW"] = prev
    run_spiffe_cli([SPIFFE_BIN, "emit-atlas", "--scenario", "rotation-boundary-trap"], env=env)
    body = read_json(SPIFFE_ATLAS)
    assert body["report_digest"] == ref["report_digest"]
