"""Behavioral verifier for fw-risk-map translation risk pipeline (independent_risk_map oracle)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from independent_risk_map import export_report, ingest_pair, load_staging_from_state

REFERENCE_PARITY_MODULE = "reference_independent_risk_map"

APP = Path("/app")
CLI = Path("/usr/local/bin/fw-risk-map")
PAIRS = APP / "fixtures/pairs"
OUTPUT = APP / "output"
STATE = APP / "state"
RESET = APP / "scripts/reset-state.sh"
TB3 = Path("/opt/verifier-fixtures/tb3-pairs")
PARTIAL_HOOKS = Path(__file__).resolve().parent / "traps/partial_hooks"
LIB = APP / "lib"

BUNDLED_PAIRS = [
    "simple-accept",
    "policy-mismatch",
    "counter-drift",
    "order-trap",
    "unsupported-recent",
]

OUTPUT_REPORT_PATH = "/app/output/translation-risk-report.json"
STATE_STAGING_META = "/app/state/staging-meta.json"
STATE_IPTABLES_TUPLES = "/app/state/iptables-tuples.ndjson"
STATE_NFT_TUPLES = "/app/state/nft-tuples.ndjson"
STATE_RUN_SEQ = "/app/state/run-seq.json"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def pair_manifest(pair_id: str) -> Path:
    if pair_id == "tb3-match-trap":
        return TB3 / "match-trap" / "pair.json"
    if pair_id == "tb3-limit-skip":
        return TB3 / "limit-skip" / "pair.json"
    return PAIRS / pair_id / "pair.json"


def ingest_cli(pair_id: str) -> subprocess.CompletedProcess[str]:
    manifest = pair_manifest(pair_id)
    return run([str(CLI), "ingest", "--pair", str(manifest)])


def export_cli(pair_id: str, out: Path) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    return run([str(CLI), "export", "--pair", pair_id, "--output", str(out)])


def reference_report(pair_id: str) -> dict:
    return export_report(ingest_pair(pair_manifest(pair_id)), run_seq=1)


def install_partial(name: str) -> None:
    src = PARTIAL_HOOKS / name
    dest = LIB / name
    data = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    dest.write_bytes(data)


def snapshot_lib() -> dict[str, str]:
    return {str(p): p.read_text(encoding="utf-8") for p in sorted(LIB.glob("*.sh"))}


def restore_lib(saved: dict[str, str]) -> None:
    for path, content in saved.items():
        Path(path).write_text(content, encoding="utf-8")


def test_cli_installed() -> None:
    """fw-risk-map CLI is on PATH and ingest without --pair exits 2."""
    assert CLI.is_file()
    proc = run([str(CLI), "ingest"])
    assert proc.returncode == 2


def test_ingest_writes_staging_files() -> None:
    """Ingest writes staging NDJSON and staging-meta under /app/state/staging-meta.json paths."""
    proc = ingest_cli("simple-accept")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert (STATE / "staging-meta.json").is_file()
    assert (STATE / "iptables-tuples.ndjson").is_file()
    assert (STATE / "nft-tuples.ndjson").is_file()


def test_staging_meta_matches_reference() -> None:
    """Staging digest and tuple counts match independent_risk_map oracle."""
    ingest_cli("simple-accept")
    ref = ingest_pair(pair_manifest("simple-accept"))
    meta = json.loads((STATE / "staging-meta.json").read_text(encoding="utf-8"))
    assert meta["pair_id"] == ref["pair_id"]
    assert meta["staging_digest"] == ref["staging_digest"]
    assert meta["tuple_counts"] == ref["tuple_counts"]


def test_export_before_ingest_exits_3() -> None:
    """Export without prior ingest for the pair exits 3."""
    proc = export_cli("simple-accept", OUTPUT / "early.json")
    assert proc.returncode == 3


def test_export_report_schema() -> None:
    """Export emits translation-risk-report.json with required schema keys."""
    ingest_cli("simple-accept")
    out = OUTPUT / "simple-schema.json"
    proc = export_cli("simple-accept", out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    report = json.loads(out.read_text(encoding="utf-8"))
    for key in (
        "schema_version",
        "pair_id",
        "staging_digest",
        "run_seq",
        "summary",
        "findings",
        "unsupported",
        "counter_drift",
        "policy_precedence",
    ):
        assert key in report
    assert report["schema_version"] == "1"


@pytest.mark.parametrize("pair_id", BUNDLED_PAIRS)
def test_report_matches_reference(pair_id: str) -> None:
    """Each bundled pair report matches independent_risk_map export."""
    ingest_cli(pair_id)
    out = OUTPUT / f"{pair_id}-ref.json"
    proc = export_cli(pair_id, out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads(out.read_text(encoding="utf-8"))
    want = reference_report(pair_id)
    assert got["staging_digest"] == want["staging_digest"]
    assert got["summary"] == want["summary"]
    assert got["findings"] == want["findings"]
    assert got["unsupported"] == want["unsupported"]
    assert got["counter_drift"] == want["counter_drift"]


def test_simple_accept_clean_summary() -> None:
    """simple-accept pair has zero high and medium findings."""
    ingest_cli("simple-accept")
    out = OUTPUT / "simple-clean.json"
    export_cli("simple-accept", out)
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["summary"]["high"] == 0
    assert report["summary"]["medium"] == 0


def test_policy_mismatch_high_finding() -> None:
    """policy-mismatch emits chain_policy_precedence high severity finding."""
    ingest_cli("policy-mismatch")
    out = OUTPUT / "policy.json"
    export_cli("policy-mismatch", out)
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["summary"]["high"] >= 1
    assert any(f["category"] == "chain_policy_precedence" for f in report["findings"])


def test_counter_drift_medium() -> None:
    """counter-drift records medium counter_preservation findings."""
    ingest_cli("counter-drift")
    out = OUTPUT / "counter.json"
    export_cli("counter-drift", out)
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["summary"]["medium"] >= 1
    assert report["counter_drift"]


def test_order_trap_rule_ordering() -> None:
    """order-trap flags rule_ordering category in findings."""
    ingest_cli("order-trap")
    out = OUTPUT / "order.json"
    export_cli("order-trap", out)
    report = json.loads(out.read_text(encoding="utf-8"))
    assert any(f["category"] == "rule_ordering" for f in report["findings"])


def test_unsupported_recent_recorded() -> None:
    """unsupported-recent lists recent in unsupported module array."""
    ingest_cli("unsupported-recent")
    out = OUTPUT / "recent.json"
    export_cli("unsupported-recent", out)
    report = json.loads(out.read_text(encoding="utf-8"))
    assert "recent" in report["unsupported"]


def test_export_uses_staging_only_poison() -> None:
    """Export ignores poisoned iptables source after ingest (staging-only contract)."""
    ingest_cli("simple-accept")
    manifest = pair_manifest("simple-accept")
    meta = json.loads((STATE / "staging-meta.json").read_text(encoding="utf-8"))
    digest_before = meta["staging_digest"]
    ipt = Path(json.loads(manifest.read_text(encoding="utf-8"))["iptables_path"])
    original = ipt.read_text(encoding="utf-8")
    try:
        ipt.write_text("# poisoned\n", encoding="utf-8")
        out = OUTPUT / "poison.json"
        proc = export_cli("simple-accept", out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads(out.read_text(encoding="utf-8"))
        assert report["staging_digest"] == digest_before
        assert report["summary"]["high"] == 0
    finally:
        ipt.write_text(original, encoding="utf-8")


def test_run_seq_stable_on_repeat_ingest() -> None:
    """Re-ingesting the same pair leaves /app/state/run-seq.json unchanged."""
    ingest_cli("simple-accept")
    seq1 = json.loads((STATE / "run-seq.json").read_text())["run_seq"]
    ingest_cli("simple-accept")
    seq2 = json.loads((STATE / "run-seq.json").read_text())["run_seq"]
    assert seq1 == seq2


def test_run_seq_increments_on_new_pair() -> None:
    """Ingesting a new pair fingerprint increments run_seq."""
    ingest_cli("simple-accept")
    seq1 = json.loads((STATE / "run-seq.json").read_text())["run_seq"]
    ingest_cli("policy-mismatch")
    seq2 = json.loads((STATE / "run-seq.json").read_text())["run_seq"]
    assert seq2 == seq1 + 1


def test_chain_policy_counters_on_staging() -> None:
    """Chain policy lines preserve bracket counters in iptables staging tuples."""
    ingest_cli("simple-accept")
    lines = (STATE / "iptables-tuples.ndjson").read_text(encoding="utf-8").splitlines()
    rows = [json.loads(raw) for raw in lines if raw.strip()]
    input_pol = [row for row in rows if row["chain"] == "INPUT" and row["ordinal"] == 0]
    assert input_pol
    assert input_pol[0]["counter_packets"] == 1200
    assert input_pol[0]["counter_bytes"] == 98400


def test_tb3_match_trap_hidden_pair() -> None:
    """TB3 match-trap under /opt/verifier-fixtures/tb3-pairs matches reference findings."""
    proc = ingest_cli("tb3-match-trap")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    out = OUTPUT / "tb3-match.json"
    proc2 = export_cli("tb3-match-trap", out)
    assert proc2.returncode == 0
    got = json.loads(out.read_text(encoding="utf-8"))
    want = export_report(ingest_pair(pair_manifest("tb3-match-trap")), run_seq=1)
    assert got["findings"] == want["findings"]


def test_tb3_limit_unsupported_hidden() -> None:
    """TB3 limit-skip pair records limit in unsupported features via verifier-fixtures."""
    proc = ingest_cli("tb3-limit-skip")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    out = OUTPUT / "tb3-limit.json"
    export_cli("tb3-limit-skip", out)
    report = json.loads(out.read_text(encoding="utf-8"))
    assert "limit" in report["unsupported"]


def test_decoy_not_on_path() -> None:
    """Decoy xtables-translate.sh is not part of the fw-risk-map hot path."""
    decoy = APP / "decoy/xtables-translate.sh"
    assert decoy.is_file()
    proc = run(["bash", str(decoy)])
    assert proc.returncode != 0


def test_partial_export_only_trap_fails() -> None:
    """Partial export.sh that reopens sources fails poison-pill staging digest trap."""
    saved = snapshot_lib()
    try:
        ingest_cli("simple-accept")
        digest_before = json.loads((STATE / "staging-meta.json").read_text())["staging_digest"]
        install_partial("export.sh")
        manifest = pair_manifest("simple-accept")
        ipt = Path(json.loads(manifest.read_text(encoding="utf-8"))["iptables_path"])
        original = ipt.read_text(encoding="utf-8")
        try:
            ipt.write_text("# poison\n", encoding="utf-8")
            out = OUTPUT / "partial-export.json"
            proc = export_cli("simple-accept", out)
            assert proc.returncode == 0
            report = json.loads(out.read_text(encoding="utf-8"))
            assert report["staging_digest"] != digest_before
        finally:
            ipt.write_text(original, encoding="utf-8")
    finally:
        restore_lib(saved)


def test_partial_ingest_only_trap_fails() -> None:
    """Partial ingest.sh breaks staging digest vs independent_risk_map oracle."""
    saved = snapshot_lib()
    try:
        install_partial("ingest.sh")
        proc = ingest_cli("simple-accept")
        assert proc.returncode == 0
        assert (STATE / "staging-meta.json").is_file()
        meta = json.loads((STATE / "staging-meta.json").read_text())
        ref = ingest_pair(pair_manifest("simple-accept"))
        assert meta["staging_digest"] != ref["staging_digest"]
    finally:
        restore_lib(saved)


def test_match_normalization_ct_sorting() -> None:
    """Match normalization sorts ctstate tokens in staging match_key."""
    ingest_cli("simple-accept")
    tuples = []
    for raw in (STATE / "iptables-tuples.ndjson").read_text().splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        if row["ordinal"] > 0:
            tuples.append(row)
    ct_rules = [t for t in tuples if "ct=" in t["match_key"]]
    assert ct_rules
    assert "ct=established,related" in ct_rules[0]["match_key"]


def test_findings_sorted() -> None:
    """Findings are sorted by category, chain, and iptables ordinal."""
    ingest_cli("order-trap")
    out = OUTPUT / "sorted.json"
    export_cli("order-trap", out)
    findings = json.loads(out.read_text())["findings"]
    keys = [(f["category"], f["chain"], f["iptables_ordinal"] or 0) for f in findings]
    assert keys == sorted(keys)


def test_load_staging_roundtrip() -> None:
    """load_staging_from_state roundtrips counter_drift vs reference export."""
    ingest_cli("counter-drift")
    staging = load_staging_from_state(STATE)
    report = export_report(staging, run_seq=1)
    out = OUTPUT / "roundtrip.json"
    export_cli("counter-drift", out)
    got = json.loads(out.read_text())
    assert got["counter_drift"] == report["counter_drift"]


def test_instruction_named_state_and_output_paths_exist() -> None:
    """Covers /app/state/staging-meta.json, iptables-tuples.ndjson, nft-tuples.ndjson, run-seq.json and /app/output/translation-risk-report.json"""
    proc = ingest_cli("simple-accept")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert (STATE / "staging-meta.json").samefile(STATE_STAGING_META)
    assert (STATE / "iptables-tuples.ndjson").samefile(STATE_IPTABLES_TUPLES)
    assert (STATE / "nft-tuples.ndjson").samefile(STATE_NFT_TUPLES)
    assert (STATE / "run-seq.json").samefile(STATE_RUN_SEQ)
    out = OUTPUT / "translation-risk-report.json"
    assert str(out) == OUTPUT_REPORT_PATH
    proc2 = export_cli("simple-accept", out)
    assert proc2.returncode == 0, proc2.stderr or proc.stdout
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["pair_id"] == "simple-accept"
