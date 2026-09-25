"""Core fluxpress contract tests against residual-occupancy docs and reference math."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/app/scripts")
from campaign_cli import rebuild, run_bind, run_seal  # noqa: E402
from fluxpress_validate import (  # noqa: E402
    build_channels,
    closure_digest,
    load_bundle,
    load_config,
    rank_channels,
    reference_atlas,
    scan_occupancy,
)


@pytest.fixture(scope="session", autouse=True)
def _rebuild_once():
    rebuild()
    yield


@pytest.fixture(autouse=True)
def _clean():
    shutil.rmtree("/app/scratch/ring-fluence", ignore_errors=True)
    shutil.rmtree("/app/output", ignore_errors=True)
    Path("/app/scratch/ring-fluence").mkdir(parents=True, exist_ok=True)
    Path("/app/output").mkdir(parents=True, exist_ok=True)
    yield


def _seal_ok(campaign: str, bundle: str, env: dict[str, str] | None = None) -> dict:
    cfg = load_config()
    b = load_bundle(cfg["bundle_dir"], bundle)
    delta = int((env or {}).get("TB3_APERTURE_DELTA", "0"))
    exp = reference_atlas(campaign, b, cfg, aperture_delta=delta)
    rc = run_bind(campaign, bundle, env=env)
    assert rc.returncode == 0, rc.stderr
    out = f"/app/output/{campaign}.json"
    rc2 = run_seal(campaign, out, env=env)
    assert rc2.returncode == 0, rc2.stderr
    got = json.loads(Path(out).read_text(encoding="utf-8"))
    assert got["closure_digest"] == exp["closure_digest"]
    assert got["channel_order"] == exp["channel_order"]
    assert got["max_occupancy"] == exp["max_occupancy"]
    assert got["peak_channel_id"] == exp["peak_channel_id"]
    assert got["spill_risk"] == exp["spill_risk"]
    assert got["effective_aperture"] == exp["effective_aperture"]
    assert [r["channel_id"] for r in got["rows"]] == [r["channel_id"] for r in exp["rows"]]
    assert [r["rank"] for r in got["rows"]] == [r["rank"] for r in exp["rows"]]
    return got


def test_basic_dual_matches_reference():
    """campaign-ring-catalog.md basic-dual: two non-overlapping channels with a flat
    background and no vetoes must seal to exactly the independent reference atlas."""
    _seal_ok("ring-alpha", "basic-dual")


def test_veto_kill_excludes_channel():
    """coincidence-veto-gate.md: a channel whose quantized energy falls inside a veto window
    must be dropped from channel_order and rows entirely, while its untouched sibling channel
    survives."""
    got = _seal_ok("ring-bravo", "veto-kill")
    ids = [r["channel_id"] for r in got["rows"]]
    assert "CH-X" not in ids
    assert "CH-X" not in got["channel_order"]
    assert "CH-Y" in ids


def test_occupancy_peak_matches_reference():
    """occupancy-scan-lemma.md occupancy-peak fixture (campaign-ring-catalog.md): three
    overlapping dwell windows must force a distinct multi-channel occupancy peak and a
    spill_risk above the fixture's aperture_budget. The peak channel is compared only against
    the independent reference implementation's own scan, not a hardcoded id, so the test
    tracks the lemma rather than one fixture's golden answer."""
    cfg = load_config()
    b = load_bundle(cfg["bundle_dir"], "occupancy-peak")
    channels = build_channels(b, cfg)
    ref_max, ref_peak = scan_occupancy(channels)
    got = _seal_ok("ring-charlie", "occupancy-peak")
    assert got["max_occupancy"] == ref_max
    assert got["peak_channel_id"] == ref_peak
    assert got["spill_risk"] is True


def test_quantize_edge_matches_reference():
    """micron-ev-quantize.md quantize-edge fixture: energies and widths sitting exactly on
    micron-eV rounding boundaries must round half away from zero identically to the
    independent Python reference math."""
    _seal_ok("ring-delta", "quantize-edge")


def test_rank_ladder_order():
    """residual-closure-atlas.md: rows must sort by residual_counts descending, tie-broken by
    channel_id ascending, with 1-based rank assigned in that order."""
    got = _seal_ok("ring-echo", "rank-ladder")
    ids = [r["channel_id"] for r in got["rows"]]
    assert ids == ["CH-HIGH", "CH-MID", "CH-LOW"]
    assert [r["rank"] for r in got["rows"]] == [1, 2, 3]


def test_mid_budget_spill_boundary_default():
    """occupancy-scan-lemma.md mid-budget fixture: at the default aperture_budget with no
    TB3_APERTURE_DELTA override, max_occupancy must sit exactly at effective_aperture so
    spill_risk is false."""
    got = _seal_ok("ring-foxtrot", "mid-budget")
    assert got["max_occupancy"] == 2
    assert got["effective_aperture"] == 2
    assert got["spill_risk"] is False


def test_mid_budget_spill_boundary_with_delta():
    """occupancy-scan-lemma.md: TB3_APERTURE_DELTA=-1 at emit-occupancy time must lower
    effective_aperture below max_occupancy and flip spill_risk to true for the same ledger."""
    got = _seal_ok("ring-foxtrot-neg", "mid-budget", env={"TB3_APERTURE_DELTA": "-1"})
    assert got["effective_aperture"] == 1
    assert got["spill_risk"] is True


def test_decoy_stub_not_required():
    """fluxpress-workflow.md / instruction.md decoy note: /app/decoy/regatlas_ir_stub.rs is an
    intentionally unused legacy stub that must never be declared as a module from /app/src/lib.rs,
    so it stays off the accrue-residuals / emit-occupancy hot path entirely."""
    decoy = Path("/app/decoy/regatlas_ir_stub.rs").read_text(encoding="utf-8")
    assert "unused" in decoy.lower() or "stub" in decoy.lower()
    lib_src = Path("/app/src/lib.rs").read_text(encoding="utf-8")
    assert "decoy" not in lib_src


def test_digest_naive_field_order_diverges():
    """Case depth: correct rank order alone does not define closure_digest key canonicalization;
    residual-closure-atlas.md requires sorted-key compact JSON, so a naive declaration-order
    digest of the same atlas must diverge from the canonical one."""
    cfg = load_config()
    b = load_bundle(cfg["bundle_dir"], "rank-ladder")
    channels = build_channels(b, cfg)
    rows = rank_channels(channels)
    atlas = {
        "campaign_id": "ring-echo",
        "effective_aperture": 5,
        "channel_order": [c["channel_id"] for c in channels if not c["vetoed"]],
        "max_occupancy": 1,
        "peak_channel_id": rows[0]["channel_id"],
        "spill_risk": False,
        "rows": rows,
    }
    good = closure_digest(atlas)
    naive = json.dumps(atlas, sort_keys=False, separators=(",", ":"))
    bad = hashlib.sha256(naive.encode("utf-8")).hexdigest()
    assert good != bad


def test_subprocess_cli_unknown_verb_nonzero():
    """instruction.md CLI surface: /app/bin/fluxpress must reject unknown verbs via subprocess
    with a non-zero exit status."""
    proc = subprocess.run(
        ["/app/bin/fluxpress", "not-a-verb"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def test_reference_residual_counts_match_python():
    """residual-lemma.md: accrue-residuals must persist residual_counts that match the
    independent reference_atlas channel math for the basic-dual fixture."""
    cfg = load_config()
    bundle = load_bundle(cfg["bundle_dir"], "basic-dual")
    ref = reference_atlas("ring-ref", bundle, cfg)
    assert run_bind("ring-ref", "basic-dual").returncode == 0
    art = json.loads(Path("/app/scratch/ring-fluence/ring-ref.json").read_text(encoding="utf-8"))
    ref_by_id = {c["channel_id"]: c["residual_counts"] for c in ref["rows"]}
    for ch in art["channels"]:
        if not ch["vetoed"]:
            assert ch["residual_counts"] == ref_by_id[ch["channel_id"]]


def test_fluence_ledger_channels_energy_sorted():
    """energy-order-lemma.md: persisted ledger channels must be sorted by energy_q ascending,
    tie-broken by channel_id ascending."""
    assert run_bind("ring-sort", "rank-ladder").returncode == 0
    art = json.loads(Path("/app/scratch/ring-fluence/ring-sort.json").read_text(encoding="utf-8"))
    keys = [(c["energy_q"], c["channel_id"]) for c in art["channels"]]
    assert keys == sorted(keys)


def test_atlas_output_trailing_newline():
    """residual-closure-atlas.md: emitted atlas files must end with exactly one trailing
    newline after the pretty-printed JSON body."""
    assert run_bind("ring-nl", "basic-dual").returncode == 0
    out = "/app/output/nl.json"
    assert run_seal("ring-nl", out).returncode == 0
    raw = Path(out).read_bytes()
    assert raw.endswith(b"\n")
    assert not raw.endswith(b"\n\n")
