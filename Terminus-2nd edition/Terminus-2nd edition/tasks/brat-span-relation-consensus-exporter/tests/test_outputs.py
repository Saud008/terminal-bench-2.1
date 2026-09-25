"""Behavioral tests for bratctl annotation consensus exporter."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from reference_consensus import reference_export

APP = Path("/app")
CLI = Path("/usr/local/bin/bratctl")
RESET = APP / "scripts" / "reset-state.sh"
STAGING = APP / "state" / "annotation-stage.json"
STAGING_SEQ = APP / "state" / "staging-seq.json"
CONSENSUS_GEN = APP / "state" / "consensus-generation.json"
EXPORT = APP / "output" / "consensus-export.json"
ALPHA = APP / "fixtures" / "projects" / "alpha"
REVISION = APP / "fixtures" / "projects" / "revision-trap"
TIE = APP / "fixtures" / "projects" / "tie-cases"
HIDDEN = Path(__file__).resolve().parent / "data" / "hidden-project"


def run(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    merged["PATH"] = "/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:" + merged.get("PATH", "")
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def ingest(project: Path) -> None:
    proc = run([str(CLI), "ingest", "--project", str(project)])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def consensus() -> None:
    proc = run([str(CLI), "consensus"])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def export_consensus() -> subprocess.CompletedProcess[str]:
    return run([str(CLI), "export"])


def pipeline(project: Path) -> None:
    ingest(project)
    consensus()
    proc = export_consensus()
    assert proc.returncode == 0, proc.stderr + proc.stdout


def setup_function() -> None:
    reset()


def test_cli_binary_exists() -> None:
    """cli-surface.md requires bratctl at /usr/local/bin/bratctl."""
    assert CLI.is_file()


def test_alpha_fixture_exists() -> None:
    """fixture-catalog.md cites alpha project under /app/fixtures/projects/alpha."""
    assert (ALPHA / "project.json").is_file()
    assert (ALPHA / "annotations").is_dir()


def test_ingest_writes_annotation_staging() -> None:
    """Ingest must write /app/state/annotation-stage.json with project metadata."""
    ingest(ALPHA)
    assert STAGING.is_file()
    body = json.loads(STAGING.read_text(encoding="utf-8"))
    assert body["project_id"] == "alpha"


def test_staging_seq_monotonic() -> None:
    """staging-seq.json increments staging_generation on every ingest."""
    ingest(ALPHA)
    first = json.loads(STAGING_SEQ.read_text(encoding="utf-8"))["staging_generation"]
    ingest(ALPHA)
    second = json.loads(STAGING_SEQ.read_text(encoding="utf-8"))["staging_generation"]
    assert second == first + 1


def test_staging_rows_revision_normalized() -> None:
    """revision-map.md: staged rows must already use current-revision coordinates."""
    ingest(REVISION)
    body = json.loads(STAGING.read_text(encoding="utf-8"))
    evt = [s for s in body["spans"] if s["label"] == "EVT"]
    assert evt
    for s in evt:
        assert s["revision"] == 2
        assert s["start"] == 15
        assert s["end"] == 25


def test_consensus_writes_generation_file() -> None:
    """consensus subcommand writes /app/state/consensus-generation.json."""
    pipeline(ALPHA)
    assert CONSENSUS_GEN.is_file()


def test_export_writes_consensus_output() -> None:
    """export subcommand writes /app/output/consensus-export.json."""
    pipeline(ALPHA)
    assert EXPORT.is_file()


def test_overlap_org_span_bob_weight_wins() -> None:
    """overlap-resolution.md picks highest-weight overlapping ORG span boundaries."""
    pipeline(ALPHA)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    org = next(s for s in got["spans"] if s["label"] == "ORG" and s["doc_id"] == "doc01")
    assert org["start"] == 12
    assert org["end"] == 20


def test_adjudication_lock_beats_higher_weight_unlocked() -> None:
    """Lower-weight adjudicator lock must survive overlapping higher-weight unlocked PER."""
    pipeline(ALPHA)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    per_spans = [s for s in got["spans"] if s["doc_id"] == "doc02" and s["label"] == "PER"]
    assert len(per_spans) == 1
    locked = per_spans[0]
    assert locked["locked"] is True
    assert locked["start"] == 0
    assert locked["end"] == 8
    assert locked["score"] == 1000.0


def test_non_adjudicator_lock_ignored() -> None:
    """alice declares a lock but is not adjudicator; only lead lock may set locked true."""
    ingest(ALPHA)
    body = json.loads(STAGING.read_text(encoding="utf-8"))
    alice_per = next(
        s for s in body["spans"] if s["annotator"] == "alice" and s["label"] == "PER"
    )
    lead_per = next(
        s for s in body["spans"] if s["annotator"] == "lead" and s["label"] == "PER"
    )
    assert alice_per["locked"] is False
    assert lead_per["locked"] is True


def test_relation_direction_arg1_before_arg2() -> None:
    """relation-direction.md exports located_in with ORG arg1_span before LOC arg2_span."""
    pipeline(ALPHA)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    org = next(s for s in got["spans"] if s["label"] == "ORG" and s["doc_id"] == "doc01")
    loc = next(s for s in got["spans"] if s["label"] == "LOC" and s["doc_id"] == "doc01")
    located = [r for r in got["relations"] if r["type"] == "located_in"]
    assert len(located) == 1
    rel = located[0]
    assert rel["arg1_span"] == org["id"]
    assert rel["arg2_span"] == loc["id"]


def test_relation_score_sums_unequal_weights() -> None:
    """Agreeing alice(1)+bob(2) located_in votes must sum to relation score 3.0."""
    pipeline(ALPHA)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    rel = next(r for r in got["relations"] if r["type"] == "located_in")
    assert rel["score"] == 3.0


def test_repeated_local_span_ids_namespace() -> None:
    """Repeated local ids s1/s2 across annotators must still map relations correctly."""
    pipeline(ALPHA)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    ref = reference_export(STAGING, CONSENSUS_GEN)
    assert got["relations"] == ref["relations"]
    assert len(got["relations"]) == 1


def test_revision_map_normalizes_offsets() -> None:
    """revision-map.md shifts revision-1 spans to current revision coordinates."""
    pipeline(REVISION)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    evt = next(s for s in got["spans"] if s["label"] == "EVT")
    assert evt["start"] == 15
    assert evt["end"] == 25


def test_longer_span_tie_break() -> None:
    """Equal-weight overlap prefers the longer MISC span on doc-long."""
    pipeline(TIE)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    misc = next(s for s in got["spans"] if s["doc_id"] == "doc-long")
    assert misc["start"] == 0
    assert misc["end"] == 8


def test_lexicographic_source_id_tie_break() -> None:
    """Equal weight and length prefers lexicographically smaller source span id."""
    pipeline(TIE)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    misc = next(s for s in got["spans"] if s["doc_id"] == "doc-lex")
    assert misc["start"] == 1
    assert misc["end"] == 5
    # earl's a-span wins over dana's z-span
    assert misc["score"] == 3.0


def test_full_alpha_export_matches_reference() -> None:
    """Independent reference agrees with subprocess pipeline on alpha project."""
    pipeline(ALPHA)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    ref = reference_export(STAGING, CONSENSUS_GEN)
    assert got == ref


def test_full_tie_cases_export_matches_reference() -> None:
    """Independent reference agrees on longer-span and lex tie-break fixture."""
    pipeline(TIE)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    ref = reference_export(STAGING, CONSENSUS_GEN)
    assert got == ref


def test_consensus_digest_sha256_prefix() -> None:
    """consensus-export-schema.md requires sha256 consensus_digest prefix."""
    pipeline(ALPHA)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    assert got["consensus_digest"].startswith("sha256:")


def test_origin_digest_matches_reference() -> None:
    """consensus_digest must match independent reference canonical payload."""
    pipeline(ALPHA)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    ref = reference_export(STAGING, CONSENSUS_GEN)
    assert got["consensus_digest"] == ref["consensus_digest"]


def test_staging_seq_path_contract() -> None:
    """Instruction cites /app/state/staging-seq.json for monotonic ingest counter."""
    ingest(ALPHA)
    assert STAGING_SEQ == Path("/app/state/staging-seq.json")
    assert STAGING_SEQ.is_file()


def test_consensus_generation_path_contract() -> None:
    """Instruction cites /app/state/consensus-generation.json for consensus state."""
    pipeline(ALPHA)
    assert CONSENSUS_GEN == Path("/app/state/consensus-generation.json")
    assert CONSENSUS_GEN.is_file()


def test_export_output_path_contract() -> None:
    """Instruction fixes export path at /app/output/consensus-export.json."""
    pipeline(ALPHA)
    assert str(EXPORT) == "/app/output/consensus-export.json"


def test_staging_path_contract() -> None:
    """Instruction fixes staging path at /app/state/annotation-stage.json."""
    ingest(ALPHA)
    assert STAGING == Path("/app/state/annotation-stage.json")


def test_spans_sorted_in_export() -> None:
    """consensus-export-schema.md sorts spans by doc_id and offsets in export."""
    pipeline(ALPHA)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    keys = [(s["doc_id"], s["start"], s["end"]) for s in got["spans"]]
    assert keys == sorted(keys)


def test_hidden_project_matches_independent_reference() -> None:
    """Verifier-only project under /tests/data must match independent reference export."""
    assert (HIDDEN / "project.json").is_file()
    pipeline(HIDDEN)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    ref = reference_export(STAGING, CONSENSUS_GEN)
    assert got == ref
    assert got["consensus_digest"] == ref["consensus_digest"]
    assert len(got["spans"]) >= 1


def test_export_reads_consensus_generation_not_live_project() -> None:
    """export must honor consensus-generation state without re-ingesting project files."""
    pipeline(ALPHA)
    gen = json.loads(CONSENSUS_GEN.read_text(encoding="utf-8"))
    gen["spans"] = []
    CONSENSUS_GEN.write_text(json.dumps(gen, indent=2) + "\n", encoding="utf-8")
    proc = export_consensus()
    assert proc.returncode == 0, proc.stderr + proc.stdout
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    assert got["spans"] == []


def test_export_rejects_staging_generation_drift() -> None:
    """Export must fail when consensus staging_generation no longer matches staging."""
    pipeline(ALPHA)
    gen = json.loads(CONSENSUS_GEN.read_text(encoding="utf-8"))
    gen["staging_generation"] = gen["staging_generation"] + 99
    CONSENSUS_GEN.write_text(json.dumps(gen, indent=2) + "\n", encoding="utf-8")
    proc = export_consensus()
    assert proc.returncode != 0


def test_export_rejects_project_digest_drift() -> None:
    """Export must fail when consensus project_digest no longer matches staging."""
    pipeline(ALPHA)
    gen = json.loads(CONSENSUS_GEN.read_text(encoding="utf-8"))
    gen["project_digest"] = "0" * 64
    CONSENSUS_GEN.write_text(json.dumps(gen, indent=2) + "\n", encoding="utf-8")
    proc = export_consensus()
    assert proc.returncode != 0


def test_independent_reference_subprocess_pipeline() -> None:
    """Subprocess ingest consensus export must match reference on alpha."""
    pipeline(ALPHA)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    assert got == reference_export(STAGING, CONSENSUS_GEN)


def test_project_digest_recorded_on_staging() -> None:
    """Ingest records project_digest on annotation staging snapshot."""
    ingest(ALPHA)
    body = json.loads(STAGING.read_text(encoding="utf-8"))
    assert len(body.get("project_digest", "")) == 64


def test_consensus_generation_increments() -> None:
    """consensus-generation.json generation counter increments per consensus run."""
    ingest(ALPHA)
    consensus()
    first = json.loads(CONSENSUS_GEN.read_text(encoding="utf-8"))["generation"]
    consensus()
    second = json.loads(CONSENSUS_GEN.read_text(encoding="utf-8"))["generation"]
    assert second == first + 1


def test_annotator_weight_reflected_in_span_score() -> None:
    """annotator-weighting.md sums weights into consensus span score for ORG overlap."""
    pipeline(ALPHA)
    got = json.loads(EXPORT.read_text(encoding="utf-8"))
    org = next(s for s in got["spans"] if s["label"] == "ORG" and s["doc_id"] == "doc01")
    assert org["score"] == 3.0


def test_consensus_witness_copies_staging_binding() -> None:
    """Consensus witness must persist staging_generation and project_digest."""
    pipeline(ALPHA)
    stage = json.loads(STAGING.read_text(encoding="utf-8"))
    gen = json.loads(CONSENSUS_GEN.read_text(encoding="utf-8"))
    assert gen["staging_generation"] == stage["staging_generation"]
    assert gen["project_digest"] == stage["project_digest"]
