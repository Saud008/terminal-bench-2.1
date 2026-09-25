"""Behavioral verifier for yaracor SOC trust correlator and sealed incident bundles."""

from __future__ import annotations

import json
import os
import random
import subprocess
from pathlib import Path

import pytest

from reference_correlate import (
    compute_events_digest,
    load_events,
    load_policy,
    policy_sha256,
    reference_correlate,
)

APP = Path("/app")
CLI = Path("/usr/local/bin/yaracor")
RESET = APP / "scripts" / "reset-state.sh"
STAGING = APP / "state" / "event-staging.json"
STAGING_SEQ = APP / "state" / "staging-seq.json"
CORRELATE_GEN = APP / "state" / "correlate-generation.json"
BUNDLE_OUT = APP / "output" / "incident-bundle.json"
REJECTED = APP / "output" / "rejected-events.jsonl"
POLICY = APP / "fixtures" / "policy" / "policy-east.json"
EVENTS = APP / "fixtures" / "events" / "alpha-scans.jsonl"
SEEDS = json.loads((APP / "fixtures" / "seeds.json").read_text(encoding="utf-8"))["seeds"]
HIDDEN = Path("/opt/verifier-fixtures/yara-delta")

def run(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    merged["PATH"] = "/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:" + merged.get("PATH", "")
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def ingest(policy: Path | None = None, events: Path | None = None, env: dict | None = None) -> None:
    proc = run(
        [
            str(CLI),
            "ingest",
            "--policy",
            str(policy or POLICY),
            "--events",
            str(events or EVENTS),
        ],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def correlate() -> None:
    proc = run([str(CLI), "correlate"])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def export_bundle() -> None:
    proc = run([str(CLI), "export"])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def pipeline(policy: Path | None = None, events: Path | None = None, env: dict | None = None) -> None:
    ingest(policy, events, env)
    correlate()
    export_bundle()


def incident_map() -> dict[str, dict]:
    body = json.loads(BUNDLE_OUT.read_text(encoding="utf-8"))
    return {row["event_id"]: row for row in body["incidents"]}


def test_instruction_output_paths_after_pipeline() -> None:
    """Full pipeline writes every instruction output path under /app/state and /app/output."""
    reset()
    pipeline()
    assert str(STAGING) == "/app/state/event-staging.json"
    assert str(STAGING_SEQ) == "/app/state/staging-seq.json"
    assert str(CORRELATE_GEN) == "/app/state/correlate-generation.json"
    assert str(BUNDLE_OUT) == "/app/output/incident-bundle.json"
    assert str(REJECTED) == "/app/output/rejected-events.jsonl"
    for path in (STAGING, STAGING_SEQ, CORRELATE_GEN, BUNDLE_OUT, REJECTED):
        assert path.is_file()


class TestIngestStaging:
    def test_ingest_writes_event_staging_path(self) -> None:
        """Ingest writes /app/state/event-staging.json with staged scan events."""
        reset()
        ingest()
        body = json.loads(STAGING.read_text(encoding="utf-8"))
        assert len(body["events"]) >= 7

    def test_events_digest_matches_reference(self) -> None:
        """Staging events_digest matches independent sha256 canonical line digest."""
        reset()
        ingest()
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        events = load_events(EVENTS)
        assert snap["events_digest"] == compute_events_digest(events)

    def test_policy_sha256_recorded(self) -> None:
        """Staging records policy_sha256 of the ingested policy file bytes."""
        reset()
        ingest()
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        assert snap["policy_sha256"] == policy_sha256(POLICY)

    def test_staging_seq_increments(self) -> None:
        """Ingest bumps /app/state/staging-seq.json staging_generation counter."""
        reset()
        ingest()
        assert str(STAGING_SEQ) == "/app/state/staging-seq.json"
        seq = json.loads(STAGING_SEQ.read_text(encoding="utf-8"))
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        assert seq["staging_generation"] == snap["staging_generation"] >= 1

    def test_rejected_events_path_after_correlate(self) -> None:
        """Correlate writes rejected-events.jsonl at the instruction output path."""
        reset()
        ingest()
        correlate()
        assert str(REJECTED) == "/app/output/rejected-events.jsonl"
        assert REJECTED.is_file()


class TestCorrelateGeneration:
    def test_correlate_bumps_generation_file(self) -> None:
        """Correlate writes /app/state/correlate-generation.json with generation at least one."""
        reset()
        ingest()
        correlate()
        gen = json.loads(CORRELATE_GEN.read_text(encoding="utf-8"))
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        assert gen["generation"] >= 1
        assert gen["staging_generation"] == snap["staging_generation"]

    def test_export_fails_after_ingest_without_correlate(self) -> None:
        """Export rejects correlate_generation zero before correlate stage runs."""
        reset()
        ingest()
        proc = run([str(CLI), "export"])
        assert proc.returncode != 0


class TestDomainRules:
    def test_stale_rule_revision_rejected(self) -> None:
        """Events outside active rule revision window land in rejected-events.jsonl."""
        reset()
        pipeline()
        lines = [json.loads(line) for line in REJECTED.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert any(r["event_id"] == "evt-005" and r["reason"] == "stale_rule_revision" for r in lines)
        rows = incident_map()
        assert "evt-005" not in rows

    def test_suppression_ticket_window(self) -> None:
        """Suppression ticket forces suppressed true for evt-002 inside ticket window."""
        reset()
        pipeline()
        row = incident_map()["evt-002"]
        assert row["suppressed"] is True
        assert row["suppression_reason"].startswith("suppression_ticket:SUP-200")
        assert row["actionable"] is False

    def test_hash_dedupe_keeps_earliest_sample(self) -> None:
        """Duplicate sample_sha256 keeps earliest detected_ms actionable."""
        reset()
        pipeline()
        keeper = incident_map()["evt-003"]
        dupe = incident_map()["evt-006"]
        assert keeper["suppressed"] is False
        assert keeper["actionable"] is True
        assert dupe["suppressed"] is True
        assert dupe["suppression_reason"] == "duplicate_sample"

    def test_criticality_escalation_after_threshold(self) -> None:
        """Asset criticality escalates one tier when detected_ms reaches escalation_ms."""
        reset()
        pipeline()
        before = incident_map()["evt-003"]
        after = incident_map()["evt-004"]
        assert before["severity_tier"] == "medium"
        assert after["severity_tier"] == "high"

    def test_quarantine_active_suppresses_sample(self) -> None:
        """Active quarantine suppresses matching sample on host-42."""
        reset()
        pipeline()
        row = incident_map()["evt-001"]
        assert row["suppressed"] is True
        assert row["suppression_reason"] == "quarantine_active"

    def test_released_quarantine_not_suppressed(self) -> None:
        """Released quarantine does not suppress events after cleared_ms."""
        reset()
        pipeline()
        row = incident_map()["evt-008"]
        assert row["suppressed"] is False
        assert row["actionable"] is True

    def test_unknown_asset_defaults_low_tier(self) -> None:
        """Assets without criticality row use default low severity tier."""
        reset()
        pipeline()
        row = incident_map()["evt-007"]
        assert row["severity_tier"] == "low"


class TestExportContract:
    def test_export_bundle_digest_present(self) -> None:
        """Export writes /app/output/incident-bundle.json with 64-char bundle_digest."""
        reset()
        pipeline()
        assert str(BUNDLE_OUT) == "/app/output/incident-bundle.json"
        body = json.loads(BUNDLE_OUT.read_text(encoding="utf-8"))
        assert len(body["bundle_digest"]) == 64
        assert body["bundle_digest"] != "pending"

    def test_export_matches_reference_correlate(self) -> None:
        """Incident bundle incidents and digest match independent reference_correlate replay."""
        reset()
        pipeline()
        policy = load_policy(POLICY)
        events = load_events(EVENTS)
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        gen = json.loads(CORRELATE_GEN.read_text(encoding="utf-8"))
        expected, exp_rejected = reference_correlate(
            policy,
            events,
            correlate_generation=gen["generation"],
            staging_generation=snap["staging_generation"],
        )
        got = json.loads(BUNDLE_OUT.read_text(encoding="utf-8"))
        assert got["incidents"] == expected["incidents"]
        assert got["bundle_digest"] == expected["bundle_digest"]
        got_rej = [json.loads(line) for line in REJECTED.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert got_rej == exp_rejected

    def test_export_rejects_tampered_staging_digest(self) -> None:
        """Export rejects tampered events_digest in event-staging snapshot."""
        reset()
        pipeline()
        snap = json.loads(STAGING.read_text(encoding="utf-8"))
        snap["events_digest"] = "0" * 64
        STAGING.write_text(json.dumps(snap, indent=2), encoding="utf-8")
        proc = run([str(CLI), "export"])
        assert proc.returncode != 0


class TestRunSubcommand:
    def test_run_executes_full_pipeline(self) -> None:
        """Run subcommand writes instruction output paths after full ingest correlate export."""
        reset()
        proc = run(
            [
                str(CLI),
                "run",
                "--policy",
                str(POLICY),
                "--events",
                str(EVENTS),
            ]
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert BUNDLE_OUT.is_file()
        assert CORRELATE_GEN.is_file()
        assert REJECTED.is_file()


class TestHiddenFixtures:
    def test_hidden_suppression_inclusive_end_ms(self) -> None:
        """Hidden delta fixture suppresses event at exactly ticket end_ms inclusive boundary."""
        reset()
        hidden_policy = HIDDEN / "policy.json"
        hidden_events = HIDDEN / "events.jsonl"
        assert str(HIDDEN).startswith("/opt/verifier-fixtures")
        pipeline(hidden_policy, hidden_events, env={"YARACOR_FIXTURE_DIR": str(HIDDEN)})
        row = incident_map()["d-101"]
        assert row["suppressed"] is True
        assert "suppression_ticket:SUP-880" in row["suppression_reason"]

    def test_hidden_rule_revision_inclusive_retired_ms(self) -> None:
        """Hidden delta fixture accepts event at exactly retired_ms inclusive boundary."""
        reset()
        hidden_policy = HIDDEN / "policy.json"
        hidden_events = HIDDEN / "events.jsonl"
        pipeline(hidden_policy, hidden_events, env={"YARACOR_FIXTURE_DIR": str(HIDDEN)})
        rows = incident_map()
        assert "d-102" in rows
        assert rows["d-102"]["actionable"] is True


class TestDecoyIsolation:
    def test_decoy_edit_does_not_change_bundle(self) -> None:
        """internal/wrap/decoy.go edits must not change incident bundle output."""
        reset()
        pipeline()
        before = BUNDLE_OUT.read_text(encoding="utf-8")
        decoy = APP / "internal/wrap/decoy.go"
        original = decoy.read_text(encoding="utf-8")
        try:
            decoy.write_text(original + "\n// decoy marker\n", encoding="utf-8")
            run(["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/yaracor"])
            reset()
            pipeline()
            after = BUNDLE_OUT.read_text(encoding="utf-8")
            assert before == after
        finally:
            decoy.write_text(original, encoding="utf-8")
            run(["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/yaracor"])


@pytest.mark.parametrize("seed", SEEDS)
def test_parametrized_ticket_and_hash_reference(seed: int, tmp_path: Path) -> None:
    """Random ticket id and sample hash per seed blocks hardcoded suppression outcomes."""
    reset()
    rng = random.Random(seed)
    policy = load_policy(POLICY)
    policy = json.loads(json.dumps(policy))
    ticket_id = f"SUP-{rng.randint(1000, 9999)}"
    sample = "".join(rng.choice("0123456789abcdef") for _ in range(64))
    start = 1700005200000 + seed * 100
    end = start + 50000
    policy["suppression_tickets"] = [
        {
            "ticket_id": ticket_id,
            "rule_name": "APT_Loader",
            "asset_id": "host-param",
            "sample_sha256": sample,
            "start_ms": start,
            "end_ms": end,
        }
    ]
    policy["asset_criticality"] = []
    policy["quarantine_states"] = []
    detected = start + 1000
    event = {
        "event_id": f"param-{seed}",
        "asset_id": "host-param",
        "sample_sha256": sample,
        "rule_name": "APT_Loader",
        "rule_revision": "rev-3",
        "detected_ms": detected,
        "scanner_host": "sensor-p",
    }
    ppath = tmp_path / f"policy-{seed}.json"
    epath = tmp_path / f"events-{seed}.jsonl"
    ppath.write_text(json.dumps(policy, indent=2), encoding="utf-8")
    epath.write_text(json.dumps(event, separators=(",", ":")) + "\n", encoding="utf-8")
    pipeline(ppath, epath)
    expected, _ = reference_correlate(policy, [event])
    got = json.loads(BUNDLE_OUT.read_text(encoding="utf-8"))
    assert got["incidents"][0] == expected["incidents"][0]


class TestProtectedDocs:
    def test_contract_docs_present(self) -> None:
        """All instruction-cited contract documents exist under /app/docs/."""
        for name in (
            "trust-policy-workflow.md",
            "soc-operator-commands.md",
            "event-staging.md",
            "rule-revisions.md",
            "suppression-windows.md",
            "hash-dedupe.md",
            "criticality-escalation.md",
            "quarantine-lifecycle.md",
            "incident-bundle-export.md",
        ):
            assert (APP / "docs" / name).is_file(), name
