"""Independent reference checks for agerecv recipient-pin admission."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

BIN = Path("/app/environment/bin/agerecv")
ENV = Path("/app/environment")
POLICY = ENV / "fixtures" / "policy" / "pins.json"
DEFAULT_CORPUS = ENV / "fixtures" / "corpus"
HIDDEN = Path("/opt/verifier-fixtures/age_hidden")
WITNESS = Path("/app/state/age-header-witness.json")
LEDGER = Path("/app/output/age-admission-ledger.json")


def _rebuild() -> None:
    subprocess.check_call(
        ["cargo", "build", "--release", "--locked", "-p", "agerecv"],
        cwd=str(ENV),
        env={**os.environ, "CARGO_TARGET_DIR": str(ENV / "target")},
    )
    BIN.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        ["install", "-D", "-m", "0755", str(ENV / "target" / "release" / "agerecv"), str(BIN)]
    )


def reference_fingerprint(type_name: str, args: list[str]) -> str:
    """Reference SHA-256 fingerprint preimage from recipient-fingerprint.md."""
    pre = type_name.upper().encode() + b"\n"
    for a in args:
        pre += a.encode() + b"\n"
    return hashlib.sha256(pre).hexdigest()


def reference_parse(path: Path) -> dict:
    """Reference age header parser used as independent oracle."""
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    i = 0
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    stanzas: list[dict] = []
    parse_ok = True
    if i >= len(lines) or lines[i].rstrip() != "age-encryption.org/v1":
        return {
            "file_id": path.stem,
            "rel_path": path.name,
            "parse_ok": False,
            "stanzas": [],
        }
    i += 1
    terminated = False
    while i < len(lines):
        t = lines[i].rstrip()
        i += 1
        if t == "---":
            terminated = True
            break
        if t.startswith("-> "):
            parts = t[3:].split()
            if not parts:
                parse_ok = False
                continue
            ty, args = parts[0], parts[1:]
            if not args or any(a == "" for a in args):
                parse_ok = False
            stanzas.append(
                {
                    "type": ty,
                    "args": args,
                    "fingerprint": reference_fingerprint(ty, args),
                }
            )
        else:
            parse_ok = False
    if not terminated:
        parse_ok = False
    return {
        "file_id": path.stem,
        "rel_path": path.name,
        "parse_ok": parse_ok,
        "stanzas": stanzas,
    }


def reference_decide(file_rec: dict, policy: dict) -> dict:
    """Reference admit/deny decision under pin-policy.md."""
    pins = set(policy["pins"])
    allow = policy["stanza_allow"]
    reasons: list[str] = []
    if not file_rec["parse_ok"]:
        return {
            "file_id": file_rec["file_id"],
            "verdict": "deny",
            "reasons": ["malformed_header"],
            "matched_pins": [],
            "stanza_count": len(file_rec["stanzas"]),
        }
    for st in file_rec["stanzas"]:
        if not any(a.upper() == st["type"].upper() for a in allow):
            reasons.append("forbidden_stanza")
            break
    if len(file_rec["stanzas"]) > policy["max_recipients"]:
        reasons.append("recipient_overflow")
    matched = sorted(
        {st["fingerprint"] for st in file_rec["stanzas"] if st["fingerprint"] in pins}
    )
    if len(matched) < policy["quorum_k"]:
        reasons.append("quorum_miss")
    if any(st["fingerprint"] not in pins for st in file_rec["stanzas"]):
        reasons.append("unpinned_recipient")
    reasons = sorted(set(reasons))
    return {
        "file_id": file_rec["file_id"],
        "verdict": "admit" if not reasons else "deny",
        "reasons": reasons,
        "matched_pins": matched,
        "stanza_count": len(file_rec["stanzas"]),
    }


def reference_admission(corpus: Path) -> tuple[dict, dict]:
    """Build reference staging snapshot and export ledger for a corpus."""
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    files = sorted(
        (reference_parse(p) for p in corpus.glob("*.age")),
        key=lambda f: f["file_id"],
    )
    decisions = [reference_decide(f, policy) for f in files]
    decisions.sort(key=lambda d: d["file_id"])
    admitted = sum(1 for d in decisions if d["verdict"] == "admit")
    denied = sum(1 for d in decisions if d["verdict"] == "deny")
    malformed = sum(1 for d in decisions if "malformed_header" in d["reasons"])
    staging_snapshot = {"files": files}
    export_ledger = {
        "decisions": decisions,
        "totals": {"admitted": admitted, "denied": denied, "malformed": malformed},
    }
    return staging_snapshot, export_ledger


def _run_pipeline(corpus: Path) -> None:
    _rebuild()
    WITNESS.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.pop("AGE_CORPUS_DIR", None)
    subprocess.check_call(
        [
            str(BIN),
            "stage-witness",
            "--corpus",
            str(corpus),
            "--policy",
            str(POLICY),
            "--witness",
            str(WITNESS),
        ],
        env=env,
    )
    subprocess.check_call(
        [
            str(BIN),
            "seal-ledger",
            "--witness",
            str(WITNESS),
            "--policy",
            str(POLICY),
            "--out",
            str(LEDGER),
        ],
        env=env,
    )


@pytest.fixture(scope="module")
def default_run():
    _run_pipeline(DEFAULT_CORPUS)
    yield


def test_t_age_ledger_schema(default_run):
    """Ledger must expose decisions and totals per admission-ledger.md."""
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert "decisions" in data and "totals" in data
    for key in ("admitted", "denied", "malformed"):
        assert key in data["totals"]


def test_t_age_alpha_admitted(default_run):
    """Corpus stem alpha must admit with empty reasons under pin policy."""
    _, ref = reference_admission(DEFAULT_CORPUS)
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    alpha = next(d for d in data["decisions"] if d["file_id"] == "alpha")
    ref_a = next(d for d in ref["decisions"] if d["file_id"] == "alpha")
    assert alpha == ref_a
    assert alpha["verdict"] == "admit"
    assert alpha["reasons"] == []


def test_t_age_bravo_forbidden_scrypt(default_run):
    """Corpus stem bravo must deny with forbidden_stanza for scrypt."""
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    bravo = next(d for d in data["decisions"] if d["file_id"] == "bravo")
    assert bravo["verdict"] == "deny"
    assert "forbidden_stanza" in bravo["reasons"]
    assert bravo["reasons"] == sorted(bravo["reasons"])


def test_t_age_charlie_quorum_miss(default_run):
    """Corpus stem charlie must deny on quorum_miss and unpinned_recipient."""
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    charlie = next(d for d in data["decisions"] if d["file_id"] == "charlie")
    assert charlie["verdict"] == "deny"
    assert "quorum_miss" in charlie["reasons"]
    assert "unpinned_recipient" in charlie["reasons"]


def test_t_age_staging_snapshot_sorted(default_run):
    """Staging snapshot witness files must sort by file_id with basename rel_path."""
    wit = json.loads(WITNESS.read_text(encoding="utf-8"))
    ids = [f["file_id"] for f in wit["files"]]
    assert ids == sorted(ids)
    for f in wit["files"]:
        assert f["rel_path"] == f"{f['file_id']}.age"


def test_t_age_fingerprint_matches_reference(default_run):
    """Stanza fingerprints must match recipient-fingerprint.md preimage."""
    staging_ref, _ = reference_admission(DEFAULT_CORPUS)
    wit = json.loads(WITNESS.read_text(encoding="utf-8"))
    for got, exp in zip(
        sorted(wit["files"], key=lambda x: x["file_id"]),
        staging_ref["files"],
        strict=True,
    ):
        assert got["file_id"] == exp["file_id"]
        assert got["stanzas"] == exp["stanzas"]


def test_t_age_export_totals_match_reference(default_run):
    """Export ledger decisions and totals must match independent reference math."""
    _, ref = reference_admission(DEFAULT_CORPUS)
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert data["totals"] == ref["totals"]
    assert data["decisions"] == ref["decisions"]


def test_t_age_ledger_idempotent(default_run):
    """Re-sealing the same staging witness must rewrite byte-identical export ledger."""
    first = LEDGER.read_bytes()
    subprocess.check_call(
        [
            str(BIN),
            "seal-ledger",
            "--witness",
            str(WITNESS),
            "--policy",
            str(POLICY),
            "--out",
            str(LEDGER),
        ]
    )
    assert LEDGER.read_bytes() == first
    assert first.endswith(b"\n")


def test_t_age_decoy_absent(default_run):
    """Decoy wrap_audit_score must not appear in sealed export ledger output."""
    text = LEDGER.read_text(encoding="utf-8")
    assert "wrap_audit_score" not in text
    assert "noise_score" not in text


def test_t_age_matched_pins_sorted(default_run):
    """Matched pin fingerprints on admit rows must be sorted ascending."""
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    for row in data["decisions"]:
        assert row["matched_pins"] == sorted(row["matched_pins"])


def test_t_age_decisions_sorted_by_file_id(default_run):
    """Export decisions must be ordered by file_id ascending."""
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    ids = [d["file_id"] for d in data["decisions"]]
    assert ids == sorted(ids)


def test_t_age_alpha_matched_pin_present(default_run):
    """Admitted alpha must list exactly one matched pin fingerprint."""
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    alpha = next(d for d in data["decisions"] if d["file_id"] == "alpha")
    assert alpha["verdict"] == "admit"
    assert len(alpha["matched_pins"]) == 1
    assert alpha["stanza_count"] == 1


def test_t_age_bravo_reasons_include_unpinned(default_run):
    """Denied bravo must also record unpinned_recipient alongside forbidden_stanza."""
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    bravo = next(d for d in data["decisions"] if d["file_id"] == "bravo")
    assert "unpinned_recipient" in bravo["reasons"]
    assert "quorum_miss" in bravo["reasons"]


def test_t_age_staging_snapshot_parse_ok(default_run):
    """Default corpus staging snapshot rows must report parse_ok true."""
    wit = json.loads(WITNESS.read_text(encoding="utf-8"))
    assert all(f["parse_ok"] for f in wit["files"])


def test_t_age_policy_quorum_k_documented(default_run):
    """Loaded pin policy quorum_k must be positive as required by pin-policy.md."""
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert int(policy["quorum_k"]) >= 1
    assert "X25519" in policy["stanza_allow"]


def test_t_age_hidden_corpus_when_present():
    """Hidden stem delta under /opt/verifier-fixtures/age_hidden must admit with two pins."""
    hidden = Path("/opt/verifier-fixtures/age_hidden")
    if not hidden.is_dir() or not any(hidden.glob("*.age")):
        pytest.skip("hidden corpus absent")
    _run_pipeline(hidden)
    _, ref = reference_admission(hidden)
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert data["decisions"] == ref["decisions"]
    assert data["totals"] == ref["totals"]
    delta = next(d for d in data["decisions"] if d["file_id"] == "delta")
    assert delta["verdict"] == "admit"
    assert len(delta["matched_pins"]) == 2


def test_t_age_tb3_hidden_trap_env_override():
    """AGE_CORPUS_DIR pointing at /opt/verifier-fixtures/age_hidden must override --corpus."""
    hidden = Path("/opt/verifier-fixtures/age_hidden")
    if not hidden.is_dir() or not any(hidden.glob("*.age")):
        pytest.skip("hidden corpus absent")
    _rebuild()
    env = {**os.environ, "AGE_CORPUS_DIR": str(hidden)}
    subprocess.check_call(
        [
            str(BIN),
            "stage-witness",
            "--corpus",
            str(DEFAULT_CORPUS),
            "--policy",
            str(POLICY),
            "--witness",
            str(WITNESS),
        ],
        env=env,
    )
    subprocess.check_call(
        [
            str(BIN),
            "seal-ledger",
            "--witness",
            str(WITNESS),
            "--policy",
            str(POLICY),
            "--out",
            str(LEDGER),
        ],
        env=env,
    )
    ids = {d["file_id"] for d in json.loads(LEDGER.read_text())["decisions"]}
    assert ids == {"delta"}


def test_t_age_malformed_header_denied(tmp_path):
    """Synthetic stem broken with bad magic must deny malformed_header."""
    bad = tmp_path / "broken.age"
    bad.write_text("not-an-age-header\n-> X25519 AAA\n---\n", encoding="utf-8")
    _run_pipeline(tmp_path)
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    broken = next(d for d in data["decisions"] if d["file_id"] == "broken")
    assert broken["verdict"] == "deny"
    assert broken["reasons"] == ["malformed_header"]
    assert data["totals"]["malformed"] == 1


def test_t_age_recipient_overflow_denied(tmp_path):
    """Four X25519 stanzas must deny with recipient_overflow under max_recipients=3."""
    # reuse alpha arg from fixture by reading alpha
    alpha = reference_parse(DEFAULT_CORPUS / "alpha.age")
    a1 = alpha["stanzas"][0]["args"][0]
    lines = ["age-encryption.org/v1"]
    for _ in range(4):
        lines.append(f"-> X25519 {a1}")
    lines.append("---")
    (tmp_path / "overflow.age").write_text("\n".join(lines) + "\n", encoding="utf-8")
    _run_pipeline(tmp_path)
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    row = next(d for d in data["decisions"] if d["file_id"] == "overflow")
    assert row["verdict"] == "deny"
    assert "recipient_overflow" in row["reasons"]
