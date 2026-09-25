"""Clerk desk redaction atlas — filing bundle bind, alias graph, risk scan, atlas emission.

Verifier probes: staging snapshot on disk after load-bundle; ingest-only path blocks export stage.
"""

from __future__ import annotations

import json

import pytest

from clerkdesk_refmath import reference_atlas_report, reference_bundle_digest
from clerkdesk_cli import (
    CLERK_SCENARIO_IDS,
    CLERK_ATLAS,
    CLERK_BIN,
    CLERK_FINDINGS,
    CLERK_FIXTURES,
    CLERK_GRAPH,
    CLERK_REV,
    CLERK_FINGERPRINT,
    clerkdesk_cli,
    clerkdesk_reset,
    read_json,
    run_clerkdesk_pipeline,
)


def test_clerkdesk_filing_atlas_smoke_load_bundle_writes_fingerprint_path() -> None:
    """load-bundle must write bundle-fingerprint.json staging snapshot under /app/state."""
    clerkdesk_reset()
    proc = clerkdesk_cli(
        [CLERK_BIN, "load-bundle", "--scenario", "party-alias-transitive", "--fixture-dir", str(CLERK_FIXTURES)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert CLERK_FINGERPRINT.is_file()


@pytest.mark.parametrize("scenario_id", CLERK_SCENARIO_IDS)
def test_clerkdesk_filing_atlas_ob01_bundle_digest_matches_refmath(scenario_id: str) -> None:
    """Bundle fingerprint digest must match independent reference math per bundle-fingerprint-contract."""
    clerkdesk_reset()
    proc = clerkdesk_cli(
        [CLERK_BIN, "load-bundle", "--scenario", scenario_id, "--fixture-dir", str(CLERK_FIXTURES)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(CLERK_FINGERPRINT.read_text(encoding="utf-8"))
    ref_digest = reference_bundle_digest(scenario_id, CLERK_FIXTURES)
    assert body["bundle_digest"] == ref_digest


def test_clerkdesk_filing_atlas_ob02_transitive_alias_links_party() -> None:
    """Transitive party alias closure must link findings to party_id P2 in party-alias-transitive scenario."""
    clerkdesk_reset()
    run_clerkdesk_pipeline("party-alias-transitive")
    report = read_json(CLERK_ATLAS)
    assert report["finding_count"] >= 1
    assert report["findings"][0]["party_id"] == "P2"


def test_clerkdesk_filing_atlas_ob03_exhibit_subref_parsed() -> None:
    """Exhibit sub-reference linkage must emit exhibit_ref Exhibit 12-A per exhibit-link-contract."""
    clerkdesk_reset()
    run_clerkdesk_pipeline("exhibit-subref-link")
    report = read_json(CLERK_ATLAS)
    assert report["findings"][0]["exhibit_ref"] == "Exhibit 12-A"


def test_clerkdesk_filing_atlas_ob04_sealed_hyphen_normalization() -> None:
    """Sealed term hyphen normalization must detect sealed-term-hyphen scenario exposure."""
    clerkdesk_reset()
    run_clerkdesk_pipeline("sealed-term-hyphen")
    report = read_json(CLERK_ATLAS)
    assert report["finding_count"] >= 1


def test_clerkdesk_filing_atlas_ob05_provenance_records_line_number() -> None:
    """Risk findings must record 1-based line citation anchors per pageline-citation-contract."""
    clerkdesk_reset()
    run_clerkdesk_pipeline("provenance-page-line")
    report = read_json(CLERK_ATLAS)
    assert report["findings"][0]["line"] == 7


def test_clerkdesk_filing_atlas_ob06_docket_primary_preferred() -> None:
    """Primary docket CV-2024-005 must win over duplicate rows per docket-dedup-contract."""
    clerkdesk_reset()
    run_clerkdesk_pipeline("docket-primary-select")
    report = read_json(CLERK_ATLAS)
    assert report["findings"][0]["docket"] == "CV-2024-005"


def test_clerkdesk_filing_atlas_ob07_party_casefold_alias_match() -> None:
    """Party alias matching must be case-insensitive per party-alias-contract."""
    clerkdesk_reset()
    run_clerkdesk_pipeline("party-casefold-match")
    report = read_json(CLERK_ATLAS)
    assert report["findings"][0]["party_id"] == "P1"


def test_clerkdesk_filing_atlas_ob08_exhibit_cross_page_scan() -> None:
    """Exhibit references must scan across multiple pages in exhibit-cross-page scenario."""
    clerkdesk_reset()
    run_clerkdesk_pipeline("exhibit-cross-page")
    report = read_json(CLERK_ATLAS)
    refs = {f["exhibit_ref"] for f in report["findings"]}
    assert "Exhibit 3" in refs


def test_clerkdesk_filing_atlas_ob09_index_parties_increments_revision() -> None:
    """index-parties must increment index_revision in index-revision.json per cli-surface."""
    clerkdesk_reset()
    clerkdesk_cli([CLERK_BIN, "load-bundle", "--scenario", "party-casefold-match", "--fixture-dir", str(CLERK_FIXTURES)])
    clerkdesk_cli([CLERK_BIN, "index-parties", "--scenario", "party-casefold-match"])
    rev = read_json(CLERK_REV)
    assert rev["index_revision"] >= 1


def test_clerkdesk_filing_atlas_ob15_index_parties_writes_party_graph() -> None:
    """index-parties must emit party-graph.json under /app/state per cli-surface."""
    clerkdesk_reset()
    clerkdesk_cli([CLERK_BIN, "load-bundle", "--scenario", "party-casefold-match", "--fixture-dir", str(CLERK_FIXTURES)])
    clerkdesk_cli([CLERK_BIN, "index-parties", "--scenario", "party-casefold-match"])
    assert CLERK_GRAPH.is_file()


def test_clerkdesk_filing_atlas_ob16_scan_risks_writes_findings_state() -> None:
    """scan-risks must emit risk-findings.json under /app/state per cli-surface."""
    clerkdesk_reset()
    clerkdesk_cli([CLERK_BIN, "load-bundle", "--scenario", "party-casefold-match", "--fixture-dir", str(CLERK_FIXTURES)])
    clerkdesk_cli([CLERK_BIN, "index-parties", "--scenario", "party-casefold-match"])
    clerkdesk_cli([CLERK_BIN, "scan-risks", "--scenario", "party-casefold-match"])
    assert CLERK_FINDINGS.is_file()


@pytest.mark.parametrize("scenario_id", ("party-casefold-match", "stable-atlas-repeat", "exhibit-subref-link"))
def test_clerkdesk_filing_atlas_ob10_atlas_report_matches_refmath(scenario_id: str) -> None:
    """Full atlas emission must match independent reference math per verifier-refmath-contract."""
    clerkdesk_reset()
    run_clerkdesk_pipeline(scenario_id)
    body = read_json(CLERK_ATLAS)
    ref = reference_atlas_report(scenario_id, CLERK_FIXTURES)
    assert body["findings"] == ref["findings"]
    assert body["atlas_digest"] == ref["atlas_digest"]


def test_clerkdesk_filing_atlas_load_only_load_bundle_blocks_emit_without_index() -> None:
    """Ingest-only load-bundle without index-parties must block export emit-atlas stage."""
    clerkdesk_reset()
    clerkdesk_cli([CLERK_BIN, "load-bundle", "--scenario", "party-casefold-match", "--fixture-dir", str(CLERK_FIXTURES)])
    clerkdesk_cli([CLERK_BIN, "scan-risks", "--scenario", "party-casefold-match"])
    proc = clerkdesk_cli([CLERK_BIN, "emit-atlas", "--scenario", "party-casefold-match"])
    assert proc.returncode != 0


def test_clerkdesk_filing_atlas_ob11_emit_atlas_blocked_before_index() -> None:
    """emit-atlas must fail when index_revision is zero per atlas-emission-contract."""
    clerkdesk_reset()
    clerkdesk_cli([CLERK_BIN, "load-bundle", "--scenario", "party-casefold-match", "--fixture-dir", str(CLERK_FIXTURES)])
    clerkdesk_cli([CLERK_BIN, "scan-risks", "--scenario", "party-casefold-match"])
    proc = clerkdesk_cli([CLERK_BIN, "emit-atlas", "--scenario", "party-casefold-match"])
    assert proc.returncode != 0


def test_clerkdesk_filing_atlas_ob12_stable_repeat_atlas_bytes_on_second_emit() -> None:
    """Second emit-atlas must produce byte-identical atlas per stable-repeat emission contract."""
    clerkdesk_reset()
    run_clerkdesk_pipeline("stable-atlas-repeat")
    first = CLERK_ATLAS.read_bytes()
    proc = clerkdesk_cli([CLERK_BIN, "emit-atlas", "--scenario", "stable-atlas-repeat"])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert CLERK_ATLAS.read_bytes() == first


def test_clerkdesk_filing_atlas_ob13_findings_sorted_by_finding_id_ascending() -> None:
    """Atlas findings must sort by finding_id ascending per atlas-emission-contract."""
    clerkdesk_reset()
    run_clerkdesk_pipeline("exhibit-cross-page")
    report = read_json(CLERK_ATLAS)
    ids = [f["finding_id"] for f in report["findings"]]
    assert ids == sorted(ids)


def test_clerkdesk_filing_atlas_ob14_subprocess_cli_invokes_filingatlas_binary() -> None:
    """Pytest must drive filingatlas via subprocess CLI per verifier-refmath-contract."""
    clerkdesk_reset()
    proc = clerkdesk_cli([CLERK_BIN, "load-bundle", "--scenario", "party-alias-transitive", "--fixture-dir", str(CLERK_FIXTURES)])
    assert CLERK_BIN in proc.args[0]
    assert proc.returncode == 0
