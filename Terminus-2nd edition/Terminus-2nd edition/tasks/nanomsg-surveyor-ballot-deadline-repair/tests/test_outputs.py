"""
Verifier for ballotmesh nanomsg surveyor ballot simulation.

Independent reference_simulate mirrors /app/docs policy contracts.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

APP = Path("/app")
CLI = Path("/usr/local/bin/ballotmesh")
MESHES = APP / "fixtures" / "meshes"
HIDDEN = Path("/opt/verifier-fixtures/meshes")
OUTPUT = APP / "output"
SNAPSHOT = APP / "state" / "survey-snapshot.json"
MANIFEST = APP / "state" / "survey.manifest"
RESET = APP / "scripts" / "reset-state.sh"
BROKEN = Path("/opt/verifier-broken-ballotmesh")
BROKEN_FALLBACK = Path(__file__).resolve().parent / "broken_lib"
PATCHES = Path(__file__).resolve().parent / "patches"

HEADER_SURVEY_OFFSET = 2
HEADER_SURVEY_LEN = 16

PATCH_TARGETS = {
    "fsm": APP / "internal/surveyor/fsm.go",
    "merge": APP / "internal/ballot/merge.go",
    "session": APP / "internal/ttl/session.go",
    "header": APP / "internal/frame/header.go",
    "dedup": APP / "internal/topology/dedup.go",
    "publish": APP / "internal/export/publish.go",
}

BROKEN_FILES = {
    "fsm": "fsm.go",
    "merge": "merge.go",
    "session": "session.go",
    "header": "header.go",
    "dedup": "dedup.go",
    "publish": "publish.go",
}

PROTECTED_SHA256: dict[str, str] = {
    "001-star-complete.json": "341ee3c3d61efbc6cc3b2c16f86f5fc84b0bcde60550a826471ad4ef729c19f5",
    "002-pipe-drain-order.json": "a37b6fe221eb0f6fa4017d5505b12c33a740de62951ed394832d0f4593c43408",
    "003-deadline-partial.json": "e620bb1dc1e86d2739191a3796609e06cdcd6f44b8374022efcd783520d8158f",
    "004-reconnect-ttl.json": "07c3048dd387b2a974a952f8a2ec95a5243b91ffc25e876300f2685a91877764",
    "005-header-survey-id.json": "b5d31530b79c237dfe7dd52f8125d16fa521116c1024ebc29d039b1a619d2db8",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reset() -> None:
    subprocess.run(["bash", str(RESET)], check=True)


def _broken_root() -> Path:
    return BROKEN if BROKEN.is_dir() else BROKEN_FALLBACK


def _build() -> subprocess.CompletedProcess[str]:
    for path in PATCH_TARGETS.values():
        os.utime(path, None)
    env = {**os.environ, "PATH": "/usr/local/go/bin:/usr/local/bin:" + os.environ.get("PATH", "")}
    return subprocess.run(
        ["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/ballotmesh"],
        cwd=APP,
        capture_output=True,
        text=True,
        timeout=600,
        env=env,
    )


def _snapshot_sources() -> dict[str, str]:
    return {name: path.read_text(encoding="utf-8") for name, path in PATCH_TARGETS.items()}


def _restore_sources(saved: dict[str, str]) -> None:
    for name, content in saved.items():
        PATCH_TARGETS[name].write_text(content, encoding="utf-8")
        os.utime(PATCH_TARGETS[name], None)


def _restore_broken_sources() -> None:
    root = _broken_root()
    for name, dest in PATCH_TARGETS.items():
        shutil.copyfile(root / BROKEN_FILES[name], dest)
        os.utime(dest, None)


def _install_patch(name: str) -> None:
    dest = PATCH_TARGETS[name]
    shutil.copyfile(PATCHES / f"golden_{name}.go", dest)
    os.utime(dest, None)


@contextmanager
def _patched_module(name: str):
    saved = _snapshot_sources()
    try:
        _restore_broken_sources()
        _install_patch(name)
        proc = _build()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        yield
    finally:
        _restore_sources(saved)
        proc = _build()
        assert proc.returncode == 0, proc.stderr or proc.stdout


def _simulate(mesh_path: Path, output_path: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PATH": "/usr/local/go/bin:/usr/local/bin:" + os.environ.get("PATH", "")}
    return subprocess.run(
        [str(CLI), "simulate", "--mesh", str(mesh_path), "--output", str(output_path)],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env=env,
    )


def _load_mesh(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _table_suffix() -> str:
    return os.environ.get("VERIFIER_TABLE_SUFFIX", "") or "default"


def _decode_header(hex_str: str) -> bytes:
    if not hex_str:
        return b""
    return bytes.fromhex(hex_str)


def _parse_survey_id(header: bytes) -> str:
    if len(header) < HEADER_SURVEY_OFFSET + HEADER_SURVEY_LEN:
        return ""
    raw = header[HEADER_SURVEY_OFFSET : HEADER_SURVEY_OFFSET + HEADER_SURVEY_LEN]
    return raw.decode("ascii", errors="replace").rstrip(" ")


def _survey_id_matches(header: bytes, expected: str) -> bool:
    got = _parse_survey_id(header)
    exp = expected.rstrip(" ")
    if len(exp) > HEADER_SURVEY_LEN:
        exp = exp[:HEADER_SURVEY_LEN]
    return got == exp


def _vote_weight(topo: dict[str, Any], respondent: str) -> int:
    if topo.get("kind") != "star":
        return 1
    seen: set[str] = set()
    for edge in topo.get("edges", []):
        a, b = edge[0], edge[1]
        if a > b:
            a, b = b, a
        key = f"{a}|{b}"
        if key in seen:
            continue
        seen.add(key)
    return 1


def reference_simulate(mesh: dict[str, Any]) -> dict[str, Any]:
    """Independent simulation matching policy docs."""
    mesh = deepcopy(mesh)
    if mesh.get("default_ttl_ms", 0) <= 0:
        mesh["default_ttl_ms"] = 30000
    if not mesh.get("topology", {}).get("kind"):
        mesh.setdefault("topology", {})["kind"] = "star"

    sealed: dict[str, bool] = {}
    pending: dict[str, bool] = {}
    sealed_votes: dict[str, int] = {}
    pending_votes: dict[str, int] = {}
    pipe_drained: dict[str, bool] = {}
    latest_vote: dict[str, int] = {}
    expires: dict[str, int] = {}
    weights: dict[str, int] = {}
    state = "waiting"
    records: list[dict[str, Any]] = []
    deadline_hit = False
    respondents: set[str] = set()

    for ev in mesh["events"]:
        if ev.get("type") == "ballot" and ev.get("respondent"):
            respondents.add(ev["respondent"])

    for idx, ev in enumerate(mesh["events"]):
        rec: dict[str, Any] = {
            "event_index": idx,
            "offset_ms": ev["offset_ms"],
            "event_type": ev["type"],
        }
        et = ev["type"]
        respondent = ev.get("respondent", "")

        if et == "start":
            state = "waiting"
            for r in respondents:
                expires[r] = ev["offset_ms"] + mesh["default_ttl_ms"]
                weights[r] = _vote_weight(mesh["topology"], r)
        elif et == "ballot":
            header = _decode_header(ev.get("header_hex", ""))
            sid_ok = _survey_id_matches(header, mesh["survey_id"])
            rec.update(
                respondent=respondent,
                survey_id_header=_parse_survey_id(header),
                survey_id_ok=sid_ok,
                pipe_drained=pipe_drained.get(respondent, False),
                ttl_expires_ms=expires.get(respondent, 0),
                topology_weight=_vote_weight(mesh["topology"], respondent),
                sealed=sealed.get(respondent, False),
                tally_included=False,
                reconnect_reset=False,
            )
            state = "collecting"
            pending[respondent] = True
            latest_vote[respondent] = ev["vote"]
            rec["sealed"] = sealed.get(respondent, False)
            active = ev["offset_ms"] <= expires.get(respondent, 0)
            if not sid_ok:
                rec["reject_reason"] = "survey_id_mismatch"
            elif not active:
                rec["reject_reason"] = "ttl_expired"
            else:
                if sealed.get(respondent, False):
                    sealed_votes[respondent] = ev["vote"]
                    rec["tally_included"] = True
                else:
                    pending_votes[respondent] = ev["vote"]
                    rec["tally_included"] = False
            rec["state_after"] = state
        elif et == "pipe_drained":
            pipe_drained[respondent] = True
            rec.update(
                respondent=respondent,
                pipe_drained=True,
                survey_id_ok=False,
                sealed=False,
                tally_included=False,
                reconnect_reset=False,
            )
            if pending.get(respondent) and respondent in latest_vote:
                if expires.get(respondent, 0) >= ev["offset_ms"]:
                    sealed[respondent] = True
                    pending.pop(respondent, None)
                    sealed_votes[respondent] = latest_vote[respondent]
                    pending_votes.pop(respondent, None)
                    rec["sealed"] = True
                    rec["tally_included"] = True
                else:
                    rec["sealed"] = False
            else:
                rec["sealed"] = sealed.get(respondent, False)
            rec["state_after"] = state
        elif et == "reconnect":
            expires[respondent] = ev["offset_ms"] + mesh["default_ttl_ms"]
            rec.update(
                respondent=respondent,
                reconnect_reset=True,
                ttl_expires_ms=expires[respondent],
                pipe_drained=False,
                survey_id_ok=False,
                sealed=False,
                tally_included=False,
                state_after=state,
            )
        elif et == "deadline":
            state = "deadline"
            deadline_hit = True
            rec["state_after"] = state
        elif et == "close":
            state = "closed"
            rec["state_after"] = state

        records.append(rec)

    final: dict[str, int] = {}
    partial: list[str] = []
    if deadline_hit:
        final = dict(sealed_votes)
        partial = sorted(pending_votes.keys())

    total = sum(final[r] * weights.get(r, 1) for r in final)

    return {
        "snapshot_version": 1,
        "table_suffix": _table_suffix(),
        "mesh_id": mesh["mesh_id"],
        "survey_id": mesh["survey_id"],
        "records": records,
        "final_tally": final,
        "total_weighted": total,
        "partial_respondents": partial,
        "export_ready": True,
    }


def _assert_matches_reference(report: dict[str, Any], mesh_path: Path) -> None:
    mesh = _load_mesh(mesh_path)
    expected = reference_simulate(mesh)
    assert report["mesh_id"] == expected["mesh_id"]
    assert report["survey_id"] == expected["survey_id"]
    assert report["table_suffix"] == expected["table_suffix"]
    assert report.get("export_source") == "staging_manifest"
    assert report["final_tally"] == expected["final_tally"]
    assert report["total_weighted"] == expected["total_weighted"]
    assert report["partial_respondents"] == expected["partial_respondents"]
    assert len(report["records"]) == len(expected["records"])
    for got, want in zip(report["records"], expected["records"], strict=True):
        for key in (
            "event_index",
            "offset_ms",
            "event_type",
            "respondent",
            "survey_id_ok",
            "pipe_drained",
            "sealed",
            "tally_included",
            "reconnect_reset",
            "topology_weight",
            "state_after",
            "reject_reason",
        ):
            if key == "reject_reason":
                if want.get("reject_reason"):
                    assert got.get("reject_reason") == want.get("reject_reason")
            elif key in want:
                assert got.get(key) == want.get(key), f"{mesh_path.name} idx {got['event_index']} {key}"


@pytest.fixture(autouse=True)
def _auto_reset():
    _reset()
    yield
    _reset()


def test_cli_builds():
    """ballotmesh must compile before simulation tests run."""
    proc = _build()
    assert proc.returncode == 0, proc.stderr or proc.stdout


@pytest.mark.parametrize("mesh_file", sorted(p.name for p in MESHES.glob("*.json")))
def test_bundled_mesh_matches_reference(mesh_file: str):
    """Every bundled mesh simulation must match independent reference policy."""
    mesh_path = MESHES / mesh_file
    out_path = OUTPUT / f"report-{mesh_file}"
    proc = _simulate(mesh_path, out_path)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert SNAPSHOT.is_file(), "staging snapshot missing"
    assert MANIFEST.is_file(), "staging manifest missing"
    report = json.loads(out_path.read_text(encoding="utf-8"))
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert report["records"] == snap["records"]
    _assert_matches_reference(report, mesh_path)


@pytest.mark.parametrize(
    "mesh_file",
    ["hidden-star-double-loop.json", "hidden-deadline-reconnect-trap.json"],
)
def test_hidden_mesh_matches_reference(mesh_file: str):
    """Hidden meshes under /opt/verifier-fixtures must match reference simulation."""
    mesh_path = HIDDEN / mesh_file
    out_path = OUTPUT / f"report-hidden-{mesh_file}"
    proc = _simulate(mesh_path, out_path)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    report = json.loads(out_path.read_text(encoding="utf-8"))
    _assert_matches_reference(report, mesh_path)


def test_fixture_integrity():
    """Bundled mesh files must remain unchanged."""
    for name, digest in PROTECTED_SHA256.items():
        assert _sha256(MESHES / name) == digest


def test_export_reads_staging_only():
    """Report export_source must be staging_manifest, not mesh re-parse."""
    mesh_path = MESHES / "001-star-complete.json"
    out_path = OUTPUT / "report-staging-source.json"
    proc = _simulate(mesh_path, out_path)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["export_source"] == "staging_manifest"


def test_table_suffix_env():
    """VERIFIER_TABLE_SUFFIX must flow into report table_suffix field."""
    os.environ["VERIFIER_TABLE_SUFFIX"] = "tb3mesh"
    try:
        mesh_path = MESHES / "001-star-complete.json"
        out_path = OUTPUT / "report-suffix.json"
        proc = _simulate(mesh_path, out_path)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads(out_path.read_text(encoding="utf-8"))
        assert report["table_suffix"] == "tb3mesh"
    finally:
        os.environ.pop("VERIFIER_TABLE_SUFFIX", None)


def test_header_only_patch_insufficient():
    """Fixing header parse alone must still fail hidden reconnect deadline trap."""
    hidden = HIDDEN / "hidden-deadline-reconnect-trap.json"
    with _patched_module("header"):
        proc = _simulate(hidden, OUTPUT / "partial-header-only.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads((OUTPUT / "partial-header-only.json").read_text(encoding="utf-8"))
        with pytest.raises(AssertionError):
            _assert_matches_reference(report, hidden)


def test_decoy_wrap_fix_alone_insufficient():
    """Patching decoy ballot wrap helper must not fix export tallies."""
    wrap_path = APP / "internal" / "export" / "wrap.go"
    saved_wrap = wrap_path.read_text(encoding="utf-8")
    saved_sources = _snapshot_sources()
    try:
        _restore_broken_sources()
        proc = _build()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        wrap_path.write_text(
            saved_wrap.replace("WrapVote", "FixedWrapVote"),
            encoding="utf-8",
        )
        proc = _build()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        proc = _simulate(MESHES / "003-deadline-partial.json", OUTPUT / "decoy-wrap.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads((OUTPUT / "decoy-wrap.json").read_text(encoding="utf-8"))
        with pytest.raises(AssertionError):
            _assert_matches_reference(report, MESHES / "003-deadline-partial.json")
    finally:
        wrap_path.write_text(saved_wrap, encoding="utf-8")
        _restore_sources(saved_sources)
        proc = _build()
        assert proc.returncode == 0, proc.stderr or proc.stdout


def test_fsm_only_patch_insufficient():
    """Fixing surveyor FSM alone must still fail partial deadline meshes."""
    mesh_path = MESHES / "003-deadline-partial.json"
    with _patched_module("fsm"):
        proc = _simulate(mesh_path, OUTPUT / "partial-fsm-only.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads((OUTPUT / "partial-fsm-only.json").read_text(encoding="utf-8"))
        with pytest.raises(AssertionError):
            _assert_matches_reference(report, mesh_path)


def test_merge_only_patch_insufficient():
    """Fixing ballot merge alone must still fail pipe-drain and header meshes."""
    mesh_path = MESHES / "002-pipe-drain-order.json"
    with _patched_module("merge"):
        proc = _simulate(mesh_path, OUTPUT / "partial-merge-only.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads((OUTPUT / "partial-merge-only.json").read_text(encoding="utf-8"))
        with pytest.raises(AssertionError):
            _assert_matches_reference(report, mesh_path)


def test_session_only_patch_insufficient():
    """Fixing reconnect TTL alone must still fail hidden deadline reconnect trap."""
    hidden = HIDDEN / "hidden-deadline-reconnect-trap.json"
    with _patched_module("session"):
        proc = _simulate(hidden, OUTPUT / "partial-session-only.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads((OUTPUT / "partial-session-only.json").read_text(encoding="utf-8"))
        with pytest.raises(AssertionError):
            _assert_matches_reference(report, hidden)


def test_dedup_only_patch_insufficient():
    """Fixing topology dedup alone must still fail hidden star double-loop mesh."""
    hidden = HIDDEN / "hidden-star-double-loop.json"
    with _patched_module("dedup"):
        proc = _simulate(hidden, OUTPUT / "partial-dedup-only.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads((OUTPUT / "partial-dedup-only.json").read_text(encoding="utf-8"))
        with pytest.raises(AssertionError):
            _assert_matches_reference(report, hidden)


def test_publish_only_patch_insufficient():
    """Fixing export publish alone must still fail mesh tally reference checks."""
    mesh_path = MESHES / "001-star-complete.json"
    with _patched_module("publish"):
        proc = _simulate(mesh_path, OUTPUT / "partial-publish-only.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads((OUTPUT / "partial-publish-only.json").read_text(encoding="utf-8"))
        with pytest.raises(AssertionError):
            _assert_matches_reference(report, mesh_path)


def test_deadline_partial_excludes_unsealed_votes():
    """Deadline mesh must list pending respondents separately from final_tally."""
    mesh_path = MESHES / "003-deadline-partial.json"
    out_path = OUTPUT / "report-deadline-partial-check.json"
    proc = _simulate(mesh_path, out_path)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    report = json.loads(out_path.read_text(encoding="utf-8"))
    expected = reference_simulate(_load_mesh(mesh_path))
    assert report["partial_respondents"] == expected["partial_respondents"] == ["r2"]
    assert report["final_tally"] == expected["final_tally"] == {"r1": 4}
    assert "r2" not in report["final_tally"]


def test_star_complete_weighted_total():
    """Star topology weighted total must match full reference export policy."""
    mesh_path = MESHES / "001-star-complete.json"
    out_path = OUTPUT / "report-weighted-total.json"
    proc = _simulate(mesh_path, out_path)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    report = json.loads(out_path.read_text(encoding="utf-8"))
    _assert_matches_reference(report, mesh_path)
    assert report["total_weighted"] > 0
