"""Cargo vendor sentinel behavioral contract tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from cvls_independent_contract import (
    audit_staging,
    canonical_json,
    export_csv,
    export_report,
    full_pipeline,
    ingest_workspace,
    workspace_fingerprint,
)
from cvls_spdx_harness import (
    APP,
    BUNDLED_WORKSPACE_IDS,
    CLI,
    OUTPUT,
    RESET,
    invoke,
    load_json,
    run_inventory,
    run_attest,
    run_publish,
    run_full_chain,
    staging_manifest,
    workspace_root,
)

DECOY = APP / "decoy/cargo-metadata-query.sh"
EXAMPLE_JSON = Path("/app/output/vendor-compliance.json")
EXAMPLE_CSV = Path("/app/output/vendor-compliance.csv")
RUN_SEQ_PATH = Path("/app/state/run-seq.json")


@pytest.fixture(autouse=True)
def _reset_vendor_state() -> None:
    proc = invoke(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


class TestCvlsSpdxGovernor:
    def test_cli_rejects_missing_workspace(self) -> None:
        """inventory requires --workspace per /app/docs/cli-surface.md."""
        assert CLI.is_file()
        proc = subprocess.run(
            [str(CLI), "inventory"],
            cwd=str(APP),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 2

    def test_inventory_materializes_staging(self) -> None:
        """inventory writes ingest_complete staging per /app/docs/staging-format.md."""
        proc = run_inventory("baseline")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        data = load_json(staging_manifest("baseline"))
        assert data["ingest_complete"] is True
        assert len(data["packages"]) >= 2

    def test_attest_requires_inventory(self) -> None:
        """attest refuses when ingest_complete is missing."""
        assert run_attest("baseline").returncode == 2

    def test_publish_requires_attest(self) -> None:
        """publish exits 3 until audit_complete is set."""
        run_inventory("baseline")
        proc = run_publish("baseline", OUTPUT / "early.json", OUTPUT / "early.csv")
        assert proc.returncode == 3

    def test_worked_example_outputs_exist(self) -> None:
        """Worked example paths under /app/output are publishable."""
        run_full_chain("baseline", EXAMPLE_JSON, EXAMPLE_CSV)
        assert EXAMPLE_JSON.is_file()
        assert EXAMPLE_CSV.is_file()

    def test_fingerprint_hashes_vendor_tree(self) -> None:
        """workspace_fingerprint covers vendor bytes per staging contract."""
        run_inventory("baseline")
        meta = load_json(staging_manifest("baseline"))
        assert meta["workspace_fingerprint"] == workspace_fingerprint(workspace_root("baseline"))

    @pytest.mark.parametrize("ws_id", BUNDLED_WORKSPACE_IDS)
    def test_bundled_matches_reference_oracle(self, ws_id: str) -> None:
        """Bundled workspaces match independent contract math."""
        json_out = OUTPUT / f"{ws_id}-oracle.json"
        csv_out = OUTPUT / f"{ws_id}-oracle.csv"
        run_full_chain(ws_id, json_out, csv_out)
        got = load_json(json_out)
        want = export_report(audit_staging(ingest_workspace(workspace_root(ws_id))))
        assert got == want

    def test_json_is_compact_sorted(self) -> None:
        """JSON export is compact sorted with trailing newline per export-format.md."""
        json_out = OUTPUT / "compact.json"
        csv_out = OUTPUT / "compact.csv"
        run_full_chain("baseline", json_out, csv_out)
        raw = json_out.read_text(encoding="utf-8")
        assert raw.endswith("\n") and ": " not in raw
        assert raw == canonical_json(
            export_report(audit_staging(ingest_workspace(workspace_root("baseline"))))
        )

    def test_csv_rows_follow_schema(self) -> None:
        """CSV rows follow export-format.md column order."""
        json_out = OUTPUT / "csv.json"
        csv_out = OUTPUT / "csv.csv"
        run_full_chain("license-drift", json_out, csv_out)
        report = load_json(json_out)
        assert csv_out.read_text(encoding="utf-8") == export_csv(report)

    def test_license_drift_counter(self) -> None:
        """license-drift workspace triggers license_drift summary counter."""
        json_out = OUTPUT / "ld.json"
        run_full_chain("license-drift", json_out, OUTPUT / "ld.csv")
        assert load_json(json_out)["summary"]["license_drift"] >= 1

    def test_checksum_mismatch_counter(self) -> None:
        """checksum-mismatch workspace triggers checksum_mismatch findings."""
        json_out = OUTPUT / "cs.json"
        run_full_chain("checksum-mismatch", json_out, OUTPUT / "cs.csv")
        assert load_json(json_out)["summary"]["checksum_mismatch"] >= 1

    def test_patch_lineage_counter(self) -> None:
        """patched-lineage workspace emits patched_crate findings."""
        json_out = OUTPUT / "pt.json"
        run_full_chain("patched-lineage", json_out, OUTPUT / "pt.csv")
        assert load_json(json_out)["summary"]["patched_crate"] >= 1

    def test_duplicate_versions_counter(self) -> None:
        """duplicate-versions workspace emits duplicate_versions findings."""
        json_out = OUTPUT / "dup.json"
        run_full_chain("duplicate-versions", json_out, OUTPUT / "dup.csv")
        assert load_json(json_out)["summary"]["duplicate_versions"] >= 1

    def test_run_seq_advances_on_new_workspace(self) -> None:
        """run-seq.json advances when workspace fingerprint changes."""
        run_inventory("baseline")
        run_attest("baseline")
        first = load_json(RUN_SEQ_PATH)["run_seq"]
        run_inventory("license-drift")
        run_attest("license-drift")
        second = load_json(RUN_SEQ_PATH)["run_seq"]
        assert second > first

    def test_tb3_license_file_precedence(self) -> None:
        """Hidden workspace under /opt/verifier-fixtures/tb3-workspaces/."""
        json_out = OUTPUT / "tb3.json"
        run_full_chain("tb3-precedence-trap", json_out, OUTPUT / "tb3.csv")
        got = load_json(json_out)
        want = export_report(
            audit_staging(ingest_workspace(workspace_root("tb3-precedence-trap")))
        )
        assert got == want

    def test_tb3_export_ignores_poisoned_vendor(self) -> None:
        """Export must read staged audit only; /opt/verifier-fixtures poison trap."""
        ws_id = "tb3-staging-poison"
        run_inventory(ws_id)
        run_attest(ws_id)
        staged = load_json(staging_manifest(ws_id))
        ref = export_report(staged, run_seq=1)
        (workspace_root(ws_id) / "vendor/serde-1.0.195/LICENSE-MIT").write_text(
            "POISON\n", encoding="utf-8"
        )
        json_out = OUTPUT / "poison.json"
        proc = run_publish(ws_id, json_out, OUTPUT / "poison.csv")
        assert proc.returncode == 0
        assert load_json(json_out) == ref

    def test_decoy_not_on_export_path(self) -> None:
        """decoy cargo-metadata-query.sh is not required for publish."""
        assert DECOY.is_file()
        run_full_chain("baseline", OUTPUT / "decoy.json", OUTPUT / "decoy.csv")

    def test_audit_digest_stable(self) -> None:
        """audit_digest matches independent contract for patched-lineage."""
        run_inventory("patched-lineage")
        run_attest("patched-lineage")
        staging = load_json(staging_manifest("patched-lineage"))
        want = audit_staging(ingest_workspace(workspace_root("patched-lineage")))
        assert staging["audit_digest"] == want["audit_digest"]

    def test_report_schema_keys(self) -> None:
        """Published JSON includes schema_version, summary, and findings."""
        json_out = OUTPUT / "schema.json"
        run_full_chain("baseline", json_out, OUTPUT / "schema.csv")
        report = load_json(json_out)
        for key in (
            "schema_version",
            "workspace_id",
            "audit_digest",
            "summary",
            "findings",
            "packages",
        ):
            assert key in report

    def test_baseline_zero_findings(self) -> None:
        """clean bundled workspace produces zero findings."""
        json_out = OUTPUT / "clean.json"
        run_full_chain("baseline", json_out, OUTPUT / "clean.csv")
        report = load_json(json_out)
        assert report["findings"] == []

    def test_lock_keeps_duplicate_stanzas(self) -> None:
        """Cargo.lock parser retains duplicate name@version stanzas."""
        run_inventory("duplicate-versions")
        rows = [
            p
            for p in load_json(staging_manifest("duplicate-versions"))["packages"]
            if p["name"] == "bitflags"
        ]
        assert len(rows) == 2

    def test_reference_full_pipeline_parity(self) -> None:
        """Full pipeline parity with independent contract on checksum-mismatch."""
        json_out = OUTPUT / "full.json"
        run_full_chain("checksum-mismatch", json_out, OUTPUT / "full.csv")
        got = load_json(json_out)
        want, _ = full_pipeline(workspace_root("checksum-mismatch"))
        assert got == want
