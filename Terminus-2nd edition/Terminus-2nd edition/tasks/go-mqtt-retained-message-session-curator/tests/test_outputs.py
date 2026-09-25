"""mqttsessctl curator contract tests — journal ingest, merge, atlas emit."""

from __future__ import annotations

import json
import os
import subprocess

import pytest

from mqttsess_cli import (
    BIN,
    BROKER_SLUG,
    BUNDLED_FIXTURES,
    OFF_CATALOG_FIXTURES,
    PATHS,
    drive_full_curator_run,
    exec_mqtt,
    read_jsonl,
    wipe_workspace,
)
from mqttsess_refmath import reference_export, reference_staging


@pytest.fixture(autouse=True)
def _isolate_mqtt_workspace():
    wipe_workspace()
    yield
    wipe_workspace()


def test_t280159_mqsess_journal_staging_digest_matches_refmath():
    """ingest-journal writes staging_digest per session-staging-schema.md."""
    proc = exec_mqtt(
        [BIN, "ingest-journal", "--broker", BROKER_SLUG, "--scenario", "clean-connect", "--fixture-dir", str(BUNDLED_FIXTURES)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(PATHS["staging"].read_text(encoding="utf-8"))
    ref = reference_staging(BROKER_SLUG, "clean-connect", BUNDLED_FIXTURES)
    assert body["staging_digest"] == ref["staging_digest"]


def test_t280159_mqsess_ingest_records_broker_slug_in_staging():
    """ingest-journal records broker slug and event_count in mqtt-journal-staging.json."""
    proc = exec_mqtt(
        [BIN, "ingest-journal", "--broker", BROKER_SLUG, "--scenario", "idempotent-replay", "--fixture-dir", str(BUNDLED_FIXTURES)]
    )
    assert proc.returncode == 0
    body = json.loads(PATHS["staging"].read_text(encoding="utf-8"))
    assert body["broker"] == BROKER_SLUG
    assert body["event_count"] == 3


def test_t280159_mqsess_emit_atlas_rejects_zero_curator_seal():
    """emit-atlas rejects export when session-curator-seal.json reports zero epoch."""
    assert exec_mqtt(
        [BIN, "ingest-journal", "--broker", BROKER_SLUG, "--scenario", "clean-connect", "--fixture-dir", str(BUNDLED_FIXTURES)]
    ).returncode == 0
    blocked = exec_mqtt([BIN, "emit-atlas", "--broker", BROKER_SLUG, "--scenario", "clean-connect"])
    assert blocked.returncode != 0


def test_t280159_mqsess_merge_pass_writes_audit_and_positive_seal():
    """merge-session writes mqtt-merge-audit.json and positive curator_seal."""
    drive_full_curator_run("clean-connect")
    assert PATHS["audit"].is_file()
    seal = json.loads(PATHS["seal"].read_text(encoding="utf-8"))
    assert seal["curator_seal"] > 0
    report = json.loads(PATHS["audit"].read_text(encoding="utf-8"))
    assert report["finding_count"] == len(report.get("findings", []))
    assert isinstance(report.get("findings"), list)


@pytest.mark.parametrize("scenario", ["wildcard-plus", "wildcard-hash", "qos1-retry", "qos2-handshake"])
def test_t280159_mqsess_delivery_ledger_matches_ref_for_scenario(scenario: str):
    """delivery-ledger.jsonl rows match refmath for bundled MQTT scenarios."""
    drive_full_curator_run(scenario)
    ledger = read_jsonl(PATHS["ledger"])
    _, ref = reference_export(BROKER_SLUG, scenario, BUNDLED_FIXTURES)
    assert ledger == ref


def test_t280159_mqsess_retained_overwrite_keeps_latest_payload_in_atlas():
    """retained overwrite keeps latest retained_payload on atlas rows."""
    drive_full_curator_run("retained-overwrite")
    atlas = read_jsonl(PATHS["atlas"])
    assert any(r.get("matched") and r.get("retained_payload") == "live" for r in atlas)


def test_t280159_mqsess_retained_delete_clears_atlas_retained_payload():
    """empty retained PUBLISH clears retained_payload in subscription atlas."""
    drive_full_curator_run("retained-delete")
    atlas = read_jsonl(PATHS["atlas"])
    assert atlas == [] or all(r.get("retained_payload") == "" for r in atlas)


def test_t280159_mqsess_session_expiry_suppresses_late_offline_delivery():
    """session expiry suppresses offline deliveries after the connect window."""
    drive_full_curator_run("session-expiry")
    assert read_jsonl(PATHS["ledger"]) == []


def test_t280159_mqsess_emit_bytes_identical_on_repeated_curator_run():
    """repeated journal replay yields byte-identical atlas and ledger exports."""
    drive_full_curator_run("idempotent-replay")
    atlas_bytes = PATHS["atlas"].read_bytes()
    ledger_bytes = PATHS["ledger"].read_bytes()
    wipe_workspace()
    drive_full_curator_run("idempotent-replay")
    assert PATHS["atlas"].read_bytes() == atlas_bytes
    assert PATHS["ledger"].read_bytes() == ledger_bytes


def test_t280159_mqsess_atlas_row_order_matches_ref_wildcard_hash():
    """wildcard-hash atlas row order matches refmath stable sort contract."""
    drive_full_curator_run("wildcard-hash")
    atlas = read_jsonl(PATHS["atlas"])
    ref_atlas, _ = reference_export(BROKER_SLUG, "wildcard-hash", BUNDLED_FIXTURES)
    assert atlas == ref_atlas


def test_t280159_mqsess_clean_connect_atlas_and_retained_payload_stable():
    """clean-connect atlas rows and retained_payload match refmath export."""
    drive_full_curator_run("clean-connect")
    atlas = read_jsonl(PATHS["atlas"])
    ref_atlas, _ = reference_export(BROKER_SLUG, "clean-connect", BUNDLED_FIXTURES)
    assert atlas == ref_atlas
    assert any(r.get("retained_payload") == "21.5" for r in atlas)


def test_t280159_mqsess_qos2_handshake_atlas_matches_refmath():
    """qos2-handshake atlas rows match refmath after PUBCOMP clears inflight."""
    drive_full_curator_run("qos2-handshake")
    atlas = read_jsonl(PATHS["atlas"])
    ref_atlas, _ = reference_export(BROKER_SLUG, "qos2-handshake", BUNDLED_FIXTURES)
    assert atlas == ref_atlas


def test_t280159_mqsess_tb3_offline_poison_qos_retry_single_row():
    """hidden offline poison yields one deduplicated QoS ledger row."""
    drive_full_curator_run("hidden-offline-poison", OFF_CATALOG_FIXTURES, {"TB3_FIXTURE_DIR": str(OFF_CATALOG_FIXTURES)})
    ledger = read_jsonl(PATHS["ledger"])
    _, ref = reference_export(BROKER_SLUG, "hidden-offline-poison", OFF_CATALOG_FIXTURES)
    assert ledger == ref and len(ledger) == 1


def test_t280159_mqsess_tb3_ingest_subprocess_reads_verifier_fixture_root():
    """ingest-journal reads verifier fixture root via TB3_FIXTURE_DIR and writes matching staging digest."""
    proc = subprocess.run(
        [BIN, "ingest-journal", "--broker", BROKER_SLUG, "--scenario", "hidden-offline-poison", "--fixture-dir", str(OFF_CATALOG_FIXTURES)],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "TB3_FIXTURE_DIR": str(OFF_CATALOG_FIXTURES)},
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(PATHS["staging"].read_text(encoding="utf-8"))
    ref = reference_staging(BROKER_SLUG, "hidden-offline-poison", OFF_CATALOG_FIXTURES)
    assert body["staging_digest"] == ref["staging_digest"]
    assert body["scenario"] == "hidden-offline-poison"


def test_t280159_mqsess_tb3_session_expiry_env_overrides_connect_window():
    """TB3_SESSION_EXPIRY_MS overrides session expiry on verifier fixtures."""
    drive_full_curator_run("session-expiry")
    assert read_jsonl(PATHS["ledger"]) == []
    wipe_workspace()
    drive_full_curator_run("session-expiry", extra_env={"TB3_SESSION_EXPIRY_MS": "20000"})
    assert len(read_jsonl(PATHS["ledger"])) == 1


def test_t280159_mqsess_merge_audit_findings_count_matches_list():
    """merge-session audit finding_count equals the findings list length for qos1-retry."""
    drive_full_curator_run("qos1-retry")
    audit = json.loads(PATHS["audit"].read_text(encoding="utf-8"))
    assert isinstance(audit, dict)
    assert isinstance(audit.get("findings"), list)
    assert audit["finding_count"] == len(audit["findings"])
    assert audit["finding_count"] == 0


def test_t280159_mqsess_wildcard_plus_matches_single_level_segment():
    """wildcard-plus scenario atlas must match refmath export."""
    drive_full_curator_run("wildcard-plus")
    atlas = read_jsonl(PATHS["atlas"])
    ref_atlas, _ = reference_export(BROKER_SLUG, "wildcard-plus", BUNDLED_FIXTURES)
    assert atlas == ref_atlas
    assert len(atlas) >= 1
