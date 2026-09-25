"""Canonicalize revision gate and normalization contracts."""

from __future__ import annotations

from xsnap_refmath import normalize_snapshot, read_json
from xsnap_session import (
    XSNAP_BIN,
    XSNAP_FIX,
    XSNAP_NORM_L,
    XSNAP_REV,
    XSNAP_STAGE,
    invoke_xsnap,
    reset_xsnap_workspace,
)


def test_xsnapctl_canonicalize_bumps_revision() -> None:
    """canonicalize increments normalize_revision counter."""
    reset_xsnap_workspace()
    invoke_xsnap([XSNAP_BIN, "ingest-pair", "--scenario", "match-precedence", "--fixture-dir", str(XSNAP_FIX)])
    invoke_xsnap([XSNAP_BIN, "canonicalize", "--scenario", "match-precedence"])
    assert read_json(XSNAP_REV)["normalize_revision"] >= 1


def test_xsnapctl_publish_blocked_before_canonicalize() -> None:
    """publish-diff rejects when normalize_revision is zero."""
    reset_xsnap_workspace()
    invoke_xsnap([XSNAP_BIN, "ingest-pair", "--scenario", "stable-diff-pair", "--fixture-dir", str(XSNAP_FIX)])
    proc = invoke_xsnap([XSNAP_BIN, "publish-diff", "--scenario", "stable-diff-pair"])
    assert proc.returncode != 0


def test_xsnapctl_cluster_endpoint_weights_sum_hundred() -> None:
    """Endpoint weights normalize to sum 100."""
    reset_xsnap_workspace()
    invoke_xsnap([XSNAP_BIN, "ingest-pair", "--scenario", "weight-normalize", "--fixture-dir", str(XSNAP_FIX)])
    invoke_xsnap([XSNAP_BIN, "canonicalize", "--scenario", "weight-normalize"])
    eps = read_json(XSNAP_NORM_L)["clusters"][0]["endpoints"]
    assert sum(e["weight"] for e in eps) == 100


def test_xsnapctl_network_filters_precede_http() -> None:
    """Listener filter chains order network filters before http."""
    reset_xsnap_workspace()
    invoke_xsnap([XSNAP_BIN, "ingest-pair", "--scenario", "filter-chain-order", "--fixture-dir", str(XSNAP_FIX)])
    invoke_xsnap([XSNAP_BIN, "canonicalize", "--scenario", "filter-chain-order"])
    types = [f["type"] for f in read_json(XSNAP_NORM_L)["listeners"][0]["filter_chains"][0]["filters"]]
    assert types.index("network") < types.index("http")


def test_xsnapctl_sds_secret_refs_lowercased() -> None:
    """SDS secret references lowercased with secret/ prefix."""
    reset_xsnap_workspace()
    invoke_xsnap([XSNAP_BIN, "ingest-pair", "--scenario", "sds-ref-resolve", "--fixture-dir", str(XSNAP_FIX)])
    invoke_xsnap([XSNAP_BIN, "canonicalize", "--scenario", "sds-ref-resolve"])
    left = read_json(XSNAP_NORM_L)
    stage = read_json(XSNAP_STAGE)
    assert left["secrets"] == normalize_snapshot(stage["left"])["secrets"]
