"""G-026 midgrid subprocess tests with independent beat-grid reference helpers.

Verifiers assert staging ledger snapshot rows after ingest load-chart and export emit-audit.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

APP_ROOT = Path("/app")
CLI = APP_ROOT / "bin" / "midgrid"
RESET = APP_ROOT / "scripts" / "reset-workspace.sh"
CHART_ROOT = APP_ROOT / "fixtures" / "charts"
CHART_DIR = APP_ROOT / "state" / "chart-manifest"
TEMPO_DIR = APP_ROOT / "work" / "tempo-ledger"
GRID_DIR = APP_ROOT / "work" / "beat-grid-ledger"
NOTE_DIR = APP_ROOT / "work" / "lane-note-ledger"


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd, cwd=str(APP_ROOT), capture_output=True, text=True, check=False, env=merged
    )


def wipe() -> None:
    proc = invoke(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def chart_path(name: str, env: dict | None = None) -> Path:
    root = Path(env["TB3_CHART_DIR"]) if env and env.get("TB3_CHART_DIR") else CHART_ROOT
    return root / f"{name}.json"


def load_chart(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["chart_id"] = doc["chart_id"].lower()
    return doc


def ordered_tempo(events: list[dict]) -> list[dict]:
    return sorted(events, key=lambda e: (e["tick"], e["microseconds_per_quarter"]))


def tick_to_seconds(tick: int, ppq: int, tempo_events: list[dict]) -> float:
    evs = ordered_tempo(tempo_events)
    sec = 0.0
    for i, ev in enumerate(evs):
        start = ev["tick"]
        if tick <= start:
            return sec
        end = evs[i + 1]["tick"] if i + 1 < len(evs) else tick
        clip = min(tick, end)
        delta = clip - start
        if delta > 0:
            sec += (delta / ppq) * (ev["microseconds_per_quarter"] / 1_000_000.0)
        if tick <= end:
            return sec
    return sec


def active_meter(tick: int, meters: list[dict]) -> dict:
    active = meters[0]
    for m in sorted(meters, key=lambda x: x["tick"]):
        if m["tick"] <= tick:
            active = m
        else:
            break
    return active


def ticks_per_beat(ppq: int, meter: dict) -> int:
    return ppq * 4 // meter["denominator"]


def quantize_tick(tick: int, ppq: int, meters: list[dict], divisor: int) -> int:
    meter = active_meter(tick, meters)
    tpb = ticks_per_beat(ppq, meter)
    grid = max(1, tpb // divisor)
    return int(round(tick / grid) * grid)


def grid_spacing(ppq: int, meters: list[dict], divisor: int, tick: int) -> int:
    meter = active_meter(tick, meters)
    return max(1, ticks_per_beat(ppq, meter) // divisor)


def intervals_overlap(a0: int, a1: int, b0: int, b1: int) -> bool:
    return a0 < b1 and b0 < a1


def rejected_overlap_ids(notes: list[dict]) -> set[str]:
    rejected: set[str] = set()
    for i in range(len(notes)):
        for j in range(i + 1, len(notes)):
            a, b = notes[i], notes[j]
            if a["lane"] != b["lane"]:
                continue
            a_end = a["tick"] + a["duration"]
            b_end = b["tick"] + b["duration"]
            if intervals_overlap(a["tick"], a_end, b["tick"], b_end):
                loser = b["id"] if b["id"] > a["id"] else a["id"]
                rejected.add(loser)
    return rejected


def reference_note_rows(chart: dict, divisor: int | None = None) -> list[dict]:
    div = divisor if divisor is not None else chart["quant_divisor"]
    rejected = rejected_overlap_ids(chart["notes"])
    rows = []
    for n in chart["notes"]:
        q = quantize_tick(n["tick"], chart["ppq"], chart["time_sigs"], div)
        rows.append(
            {
                "id": n["id"],
                "lane": n["lane"],
                "raw_tick": n["tick"],
                "quantized_tick": q,
                "rejected_overlap": n["id"] in rejected,
            }
        )
    rows.sort(key=lambda r: r["id"])
    return rows


def grid_consistency_score(rows: list[dict], chart: dict, divisor: int) -> float:
    accepted = [r for r in rows if not r["rejected_overlap"]]
    if not accepted:
        return 1.0
    ok = 0
    for row in accepted:
        grid = grid_spacing(chart["ppq"], chart["time_sigs"], divisor, row["raw_tick"])
        if abs(row["raw_tick"] - row["quantized_tick"]) <= grid // 2:
            ok += 1
    return ok / len(accepted)


def audit_digest(audit: dict) -> str:
    ids = sorted(n["id"] for n in audit["notes"])
    body = json.dumps(
        {
            "accepted_note_count": audit["accepted_note_count"],
            "chart_id": audit["chart_id"],
            "rejected_overlap_count": audit["rejected_overlap_count"],
            "run_id": audit["run_id"],
            "source_ids": ids,
        },
        separators=(",", ":"),
    )
    proc = subprocess.run(
        ["python3", "/app/scripts/audit_digest_ref.py"],
        input=body,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return proc.stdout.strip()


def reference_audit(run_id: str, chart: dict, rows: list[dict], divisor: int) -> dict:
    rejected = sum(1 for r in rows if r["rejected_overlap"])
    accepted = len(rows) - rejected
    audit = {
        "run_id": run_id,
        "chart_id": chart["chart_id"],
        "ppq": chart["ppq"],
        "tempo_event_count": len(chart["tempo_events"]),
        "accepted_note_count": accepted,
        "rejected_overlap_count": rejected,
        "grid_consistency_score": grid_consistency_score(rows, chart, divisor),
        "notes": rows,
        "audit_digest": "",
    }
    audit["audit_digest"] = audit_digest(audit)
    return audit


def run_pipeline(
    run_id: str,
    chart_name: str,
    *,
    env: dict | None = None,
    quant: int | None = None,
) -> Path:
    chart = chart_path(chart_name, env)
    doc = load_chart(chart)
    div = quant if quant is not None else doc["quant_divisor"]
    if env and env.get("TB3_QUANT_DIVISOR"):
        div = int(env["TB3_QUANT_DIVISOR"])
    steps = [
        [str(CLI), "load-chart", "--run-id", run_id, "--chart", str(chart)],
        [str(CLI), "stage-tempo", "--run-id", run_id],
        [str(CLI), "build-grid", "--run-id", run_id, "--quant", str(div)],
        [str(CLI), "quantize-notes", "--run-id", run_id],
    ]
    for step in steps:
        proc = invoke(step, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP_ROOT / "output" / f"{run_id}-beat-grid-audit.json"
    proc = invoke(
        [str(CLI), "emit-audit", "--run-id", run_id, "--output", str(out)],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out


@pytest.fixture(autouse=True)
def _clean():
    wipe()
    yield
    wipe()


def test_cli_binary_exists():
    """Verifier requires midgrid installed at /app/bin/midgrid per instruction."""
    assert CLI.is_file()


def test_load_chart_manifest_schema_arcade01():
    """load-chart writes chart manifest fields per /app/docs/chart-manifest-schema.md."""
    run_id = "t-ing-01"
    chart = chart_path("arcade-01")
    ref = load_chart(chart)
    proc = invoke([str(CLI), "load-chart", "--run-id", run_id, "--chart", str(chart)])
    assert proc.returncode == 0, proc.stderr
    ledger = json.loads((CHART_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    assert ledger["chart_id"] == ref["chart_id"]
    assert ledger["ppq"] == ref["ppq"]
    assert ledger["manifest_revision"] == 1


def test_load_generation_increments():
    """Repeated load-chart bumps manifest_revision per chart-manifest persistence rules."""
    run_id = "t-gen"
    chart = chart_path("arcade-02")
    invoke([str(CLI), "load-chart", "--run-id", run_id, "--chart", str(chart)])
    invoke([str(CLI), "load-chart", "--run-id", run_id, "--chart", str(chart)])
    ledger = json.loads((CHART_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    assert ledger["manifest_revision"] == 2


def test_stage_tempo_order_arcade01():
    """stage-tempo orders tempo rows by tick per /app/docs/tempo-map-sequence.md."""
    run_id = "t-tempo-01"
    chart = chart_path("arcade-01")
    ref = load_chart(chart)
    invoke([str(CLI), "load-chart", "--run-id", run_id, "--chart", str(chart)])
    invoke([str(CLI), "stage-tempo", "--run-id", run_id])
    lines = (TEMPO_DIR / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0])["row_type"] == "header"
    ticks = [json.loads(line)["tick"] for line in lines[1:]]
    assert ticks == [e["tick"] for e in ordered_tempo(ref["tempo_events"])]


def test_tick_to_seconds_tempo_boundary_arcade01():
    """build-grid tick seconds follow tick-clock conversion across tempo boundaries."""
    run_id = "t-sec-01"
    chart = chart_path("arcade-01")
    ref = load_chart(chart)
    run_pipeline(run_id, "arcade-01")
    rows = [json.loads(line) for line in (GRID_DIR / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()[1:]]
    target = 1920
    got = next(r["seconds"] for r in rows if r["tick"] == target)
    expect = tick_to_seconds(target, ref["ppq"], ref["tempo_events"])
    assert abs(got - expect) < 0.0005


def test_meter_ticks_per_beat_arcade03():
    """beat-grid rows expose ticks_per_beat from active meter timeline contract."""
    run_id = "t-meter-03"
    chart = chart_path("arcade-03")
    ref = load_chart(chart)
    run_pipeline(run_id, "arcade-03")
    tick = 960
    meter = active_meter(tick, ref["time_sigs"])
    expect_tpb = ticks_per_beat(ref["ppq"], meter)
    rows = [json.loads(line) for line in (GRID_DIR / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()[1:]]
    got = next(r["ticks_per_beat"] for r in rows if r["tick"] == tick)
    assert got == expect_tpb


def test_quantize_nearest_arcade02():
    """quantize-notes snaps raw ticks to nearest grid per quantize-window policy."""
    run_id = "t-quant-02"
    chart = chart_path("arcade-02")
    ref = load_chart(chart)
    run_pipeline(run_id, "arcade-02")
    rows = [json.loads(line) for line in (NOTE_DIR / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()[1:]]
    expected = reference_note_rows(ref)
    for exp, got in zip(expected, rows, strict=True):
        assert got["quantized_tick"] == exp["quantized_tick"]


def test_overlap_rejection_arcade03():
    """quantize-notes flags same-lane overlaps per overlap-rejection policy."""
    run_id = "t-ov-03"
    chart = chart_path("arcade-03")
    ref = load_chart(chart)
    run_pipeline(run_id, "arcade-03")
    rows = [json.loads(line) for line in (NOTE_DIR / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()[1:]]
    expected = reference_note_rows(ref)
    for exp, got in zip(expected, rows, strict=True):
        assert got["rejected_overlap"] == exp["rejected_overlap"]


def test_emit_audit_digest_arcade01():
    """Emit-audit digest; export-stage-only patches must not skip tempo and quantize layers."""
    run_id = "t-dig-01"
    chart = chart_path("arcade-01")
    ref = load_chart(chart)
    out = run_pipeline(run_id, "arcade-01")
    audit = json.loads(out.read_text(encoding="utf-8"))
    rows = reference_note_rows(ref)
    expected = reference_audit(run_id, ref, rows, ref["quant_divisor"])
    assert audit["audit_digest"] == expected["audit_digest"]


def test_full_pipeline_arcade01():
    """Full pipeline emits beat-grid audit counts for arcade-01 under /app/output/."""
    run_id = "t-full-01"
    chart = chart_path("arcade-01")
    ref = load_chart(chart)
    rows = reference_note_rows(ref)
    expected = reference_audit(run_id, ref, rows, ref["quant_divisor"])
    out = run_pipeline(run_id, "arcade-01")
    audit = json.loads(out.read_text(encoding="utf-8"))
    assert audit["accepted_note_count"] == expected["accepted_note_count"]
    assert audit["rejected_overlap_count"] == expected["rejected_overlap_count"]
    assert abs(audit["grid_consistency_score"] - expected["grid_consistency_score"]) < 0.001


def test_full_pipeline_arcade02():
    """Full pipeline preserves tempo_event_count and audit_digest for arcade-02."""
    run_id = "t-full-02"
    chart = chart_path("arcade-02")
    ref = load_chart(chart)
    rows = reference_note_rows(ref)
    expected = reference_audit(run_id, ref, rows, ref["quant_divisor"])
    out = run_pipeline(run_id, "arcade-02")
    audit = json.loads(out.read_text(encoding="utf-8"))
    assert audit["tempo_event_count"] == expected["tempo_event_count"]
    assert audit["audit_digest"] == expected["audit_digest"]


def test_full_pipeline_arcade03():
    """Full pipeline reports overlap rejections and grid consistency for arcade-03."""
    run_id = "t-full-03"
    chart = chart_path("arcade-03")
    ref = load_chart(chart)
    rows = reference_note_rows(ref)
    expected = reference_audit(run_id, ref, rows, ref["quant_divisor"])
    out = run_pipeline(run_id, "arcade-03")
    audit = json.loads(out.read_text(encoding="utf-8"))
    assert audit["rejected_overlap_count"] >= 1
    assert audit["grid_consistency_score"] == expected["grid_consistency_score"]


def test_full_pipeline_arcade04():
    """Full pipeline honors randomized ppq on arcade-04 anti-hardcoding catalog."""
    run_id = "t-full-04"
    chart = chart_path("arcade-04")
    ref = load_chart(chart)
    rows = reference_note_rows(ref)
    expected = reference_audit(run_id, ref, rows, ref["quant_divisor"])
    out = run_pipeline(run_id, "arcade-04")
    audit = json.loads(out.read_text(encoding="utf-8"))
    assert audit["ppq"] == ref["ppq"]
    assert audit["accepted_note_count"] == expected["accepted_note_count"]


def test_tb3_hidden_chart_overlay():
    """TB3_CHART_DIR hidden overlay chart drives independent overlap audit math."""
    run_id = "t-tb3-chart"
    env = {"TB3_CHART_DIR": "/opt/verifier-fixtures/midgrid/charts"}
    chart = chart_path("tb3-swing-lane", env)
    ref = load_chart(chart)
    rows = reference_note_rows(ref, divisor=8)
    expected = reference_audit(run_id, ref, rows, 8)
    out = run_pipeline(run_id, "tb3-swing-lane", env=env, quant=8)
    audit = json.loads(out.read_text(encoding="utf-8"))
    assert audit["rejected_overlap_count"] == expected["rejected_overlap_count"]
    assert audit["audit_digest"] == expected["audit_digest"]


def test_tb3_quant_divisor_override():
    """TB3_QUANT_DIVISOR env overrides quant divisor per quantize-window policy."""
    run_id = "t-tb3-quant"
    env = {"TB3_QUANT_DIVISOR": "8"}
    chart = chart_path("arcade-01")
    ref = load_chart(chart)
    rows = reference_note_rows(ref, divisor=8)
    expected = reference_audit(run_id, ref, rows, 8)
    out = run_pipeline(run_id, "arcade-01", env=env)
    audit = json.loads(out.read_text(encoding="utf-8"))
    assert abs(audit["grid_consistency_score"] - expected["grid_consistency_score"]) < 0.001


def test_note_stage_sorted_ids():
    """lane-note ledger rows sort note ids lexicographically after quantize-notes."""
    run_id = "t-sort"
    run_pipeline(run_id, "arcade-04")
    ids = [json.loads(line)["id"] for line in (NOTE_DIR / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()[1:]]
    assert ids == sorted(ids)


def test_grid_stage_header_quant():
    """beat-grid ledger header records quant_divisor from build-grid --quant."""
    run_id = "t-grid-hdr"
    run_pipeline(run_id, "arcade-02", quant=2)
    hdr = json.loads((GRID_DIR / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert hdr["quant_divisor"] == 2


def test_tempo_event_count_matches_chart():
    """emit-audit tempo_event_count mirrors chart tempo_events length."""
    run_id = "t-tcnt"
    chart = chart_path("arcade-03")
    ref = load_chart(chart)
    out = run_pipeline(run_id, "arcade-03")
    audit = json.loads(out.read_text(encoding="utf-8"))
    assert audit["tempo_event_count"] == len(ref["tempo_events"])


def test_output_suffix_beat_grid_audit():
    """emit-audit output path ends with -beat-grid-audit.json per instruction."""
    run_id = "t-suffix"
    out = run_pipeline(run_id, "arcade-01")
    assert out.name.endswith("-beat-grid-audit.json")


def test_cross_run_reset_clears_manifest():
    """reset-workspace.sh clears /app/state/chart-manifest between verifier runs."""
    run_id = "t-reset"
    run_pipeline(run_id, "arcade-01")
    wipe()
    assert not list(CHART_DIR.glob("*.json"))


def test_decoy_module_not_required():
    """harmony_decoy stays off the midgrid export hot path per instruction."""
    assert not (APP_ROOT / "harmony_decoy" / "harmony.rs").read_text(encoding="utf-8").strip().startswith("#")


def test_beat_index_reference_arcade02():
    """beat-grid beat_index equals tick divided by ticks_per_beat at note tick."""
    run_id = "t-beat"
    chart = chart_path("arcade-02")
    ref = load_chart(chart)
    run_pipeline(run_id, "arcade-02")
    tick = ref["notes"][2]["tick"]
    meter = active_meter(tick, ref["time_sigs"])
    tpb = ticks_per_beat(ref["ppq"], meter)
    expect = tick / tpb
    rows = [json.loads(line) for line in (GRID_DIR / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()[1:]]
    got = next(r["beat_index"] for r in rows if r["tick"] == tick)
    assert abs(got - expect) < 0.0001


def test_arcade04_ppq_anti_hardcode():
    """Fixture catalog exposes multiple ppq values to block hardcoded chart constants."""
    catalog = json.loads((APP_ROOT / "fixtures" / "chart_catalog.json").read_text(encoding="utf-8"))
    ppqs = {c["ppq"] for c in catalog["charts"]}
    assert len(ppqs) >= 3
