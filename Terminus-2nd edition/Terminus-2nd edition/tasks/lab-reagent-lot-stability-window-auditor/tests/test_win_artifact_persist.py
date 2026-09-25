"""Correlation artifact persistence and session field tests."""

from __future__ import annotations

import json

from win_session_cli import CLI_BIN, SESSION_POOL, correlation_path, invoke, wipe


def test_correlation_carries_as_of_date() -> None:
    """correlation-artifact-schema.md copies as_of_date from the session bundle."""
    wipe()
    sid, bundle = SESSION_POOL[0], "dual-lot-basic"
    proc = invoke([str(CLI_BIN), "correlate", "--session", sid, "--bundle", bundle])
    assert proc.returncode == 0
    body = json.loads(correlation_path(sid).read_text(encoding="utf-8"))
    assert body["as_of_date"] == "2026-03-15"


def test_correlation_lists_all_lots() -> None:
    """correlate must materialize every lot from the dual-lot-basic session bundle."""
    wipe()
    sid, bundle = SESSION_POOL[1], "dual-lot-basic"
    proc = invoke([str(CLI_BIN), "correlate", "--session", sid, "--bundle", bundle])
    assert proc.returncode == 0
    body = json.loads(correlation_path(sid).read_text(encoding="utf-8"))
    assert len(body["lots"]) == 2


def test_correlation_includes_excursion_fields() -> None:
    """Correlated lots must expose excursion_minutes and severity integral fields."""
    wipe()
    sid, bundle = SESSION_POOL[2], "dual-lot-basic"
    proc = invoke([str(CLI_BIN), "correlate", "--session", sid, "--bundle", bundle])
    assert proc.returncode == 0
    lot = json.loads(correlation_path(sid).read_text(encoding="utf-8"))["lots"][0]
    assert "excursion_minutes" in lot
    assert "severity" in lot


def test_recorrelate_same_session_new_bundle_bumps_generation() -> None:
    """Recorrelating the same session with a new bundle updates bundle name and generation."""
    wipe()
    sid = SESSION_POOL[3]
    invoke([str(CLI_BIN), "correlate", "--session", sid, "--bundle", "dual-lot-basic"])
    invoke([str(CLI_BIN), "correlate", "--session", sid, "--bundle", "cumulative-extension"])
    body = json.loads(correlation_path(sid).read_text(encoding="utf-8"))
    assert body["correlate_generation"] == 2
    assert body["bundle"] == "cumulative-extension"


def test_correlation_cert_digest_present() -> None:
    """Every correlated lot must carry a non-empty cert_digest from provenance digest rules."""
    wipe()
    sid, bundle = SESSION_POOL[0], "cumulative-extension"
    invoke([str(CLI_BIN), "correlate", "--session", sid, "--bundle", bundle])
    body = json.loads(correlation_path(sid).read_text(encoding="utf-8"))
    assert all(lot["cert_digest"] for lot in body["lots"])
