"""Bundled shadedrift contract tests for textile dye-lot shade drift."""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

from shadedrift_contract_math import (
    cie76,
    correlate_scenario,
    drift_class,
    pick_recipe,
    read_tsv_rows,
    reference_report,
    resolve_target_lab,
)
import subprocess

from shadedrift_runner import APP, CLI, CORR_SNAP_DIR, invoke, pipeline, wipe

POLICY = APP / "config" / "shadedrift.json"
FIX = APP / "fixtures" / "scenarios"


def test_t010955_tdl01_scarlet_report_matches_reference():
    """Bundled scarlet scenario drift report matches independent reference math."""
    wipe()
    out = pipeline("scarlet-base-lot", "run-scarlet")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_report(FIX / "scarlet-base-lot", "run-scarlet", POLICY)
    assert rep["drift_rows"] == ref["drift_rows"]


def test_t010955_tdl02_corr_snap_has_readings_digest():
    """Correlated correlation snapshot under /app/state/shade-correlation/ records readings_digest."""
    wipe()
    pipeline("scarlet-base-lot", "run-digest")
    corr_snap = json.loads((CORR_SNAP_DIR / "run-digest.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256((FIX / "scarlet-base-lot" / "readings.tsv").read_bytes()).hexdigest()
    assert corr_snap["readings_digest"] == digest
    assert corr_snap["correlated"] is True


def test_t010955_tdl03_recipe_precedence_picks_latest():
    """Recipe precedence helper agrees with drift report recipe_version field."""
    recipes = json.loads((FIX / "scarlet-base-lot" / "recipes.json").read_text())["recipes"]
    picked = pick_recipe(recipes, "scarlet-vat", 1709500000, None)
    ref = reference_report(FIX / "scarlet-base-lot", "run-prec", POLICY)
    assert picked["version"] == ref["drift_rows"][0]["recipe_version"]


def test_t010955_tdl04_lineage_inherits_parent_lab():
    """Nullable target_lab inherits parent batch anchor per batch-lineage contract."""
    batches = json.loads((FIX / "mercer-lineage-chain" / "batches.json").read_text())["batches"]
    child_id = batches[1]["batch_id"]
    anchor = resolve_target_lab(batches, child_id)
    assert anchor == batches[0]["target_lab"]


def test_t010955_tdl05_cie76_reference_math():
    """CIE76 delta helper matches Euclidean LAB distance contract."""
    assert cie76(52.1, 18.2, 12.05, 51.5, 17.8, 11.5) == round((0.6**2 + 0.4**2 + 0.55**2) ** 0.5, 6)


def test_t010955_tdl06_drift_class_thresholds():
    """Drift class bands follow warn_delta_e and fail_delta_e policy thresholds."""
    policy = json.loads(POLICY.read_text())
    assert drift_class(1.0, policy["warn_delta_e"], policy["fail_delta_e"]) == "within"
    assert drift_class(3.0, policy["warn_delta_e"], policy["fail_delta_e"]) == "watch"
    assert drift_class(6.0, policy["warn_delta_e"], policy["fail_delta_e"]) == "reject"


def test_t010955_tdl07_indigo_rework_midwindow():
    """Mid-window reading keeps rework_applied and matches reference recipe_version."""
    wipe()
    rows = read_tsv_rows(FIX / "indigo-rework-window" / "readings.tsv")
    mid_key = rows[1]["reading_id"]
    out = pipeline("indigo-rework-window", "run-indigo")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_report(FIX / "indigo-rework-window", "run-indigo", POLICY)
    mid = next(r for r in rep["drift_rows"] if r["reading_id"] == mid_key)
    mid_ref = next(r for r in ref["drift_rows"] if r["reading_id"] == mid_key)
    assert mid["rework_applied"] is True
    assert mid["recipe_version"] == mid_ref["recipe_version"]


def test_t010955_tdl08_indigo_post_rework_after_window():
    """Post-rework reading clears rework_applied and matches reference recipe_version."""
    wipe()
    rows = read_tsv_rows(FIX / "indigo-rework-window" / "readings.tsv")
    late_key = rows[2]["reading_id"]
    out = pipeline("indigo-rework-window", "run-indigo2")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_report(FIX / "indigo-rework-window", "run-indigo2", POLICY)
    late = next(r for r in rep["drift_rows"] if r["reading_id"] == late_key)
    late_ref = next(r for r in ref["drift_rows"] if r["reading_id"] == late_key)
    assert late["rework_applied"] is False
    assert late["recipe_version"] == late_ref["recipe_version"]


def test_t010955_tdl09_mercer_lineage_report():
    """Mercer lineage scenario export matches independent reference rows."""
    wipe()
    out = pipeline("mercer-lineage-chain", "run-mercer")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_report(FIX / "mercer-lineage-chain", "run-mercer", POLICY)
    assert rep["drift_rows"] == ref["drift_rows"]


def test_t010955_tdl10_correlation_digest_stable():
    """correlation_digest on correlation snapshot is stable across repeated runs."""
    wipe()
    pipeline("scarlet-base-lot", "run-stable")
    d1 = json.loads((CORR_SNAP_DIR / "run-stable.json").read_text())["correlation_digest"]
    wipe()
    pipeline("scarlet-base-lot", "run-stable")
    d2 = json.loads((CORR_SNAP_DIR / "run-stable.json").read_text())["correlation_digest"]
    assert d1 == d2


def test_t010955_tdl11_export_audit_digest():
    """Drift report audit_digest hashes drift_rows per drift-report-schema."""
    wipe()
    out = pipeline("scarlet-base-lot", "run-audit")
    rep = json.loads(out.read_text(encoding="utf-8"))
    expected = hashlib.sha256(json.dumps(rep["drift_rows"], separators=(",", ":")).encode()).hexdigest()
    assert rep["audit_digest"] == expected


def test_t010955_tdl12_duplicate_reading_id_keeps_last():
    """Duplicate reading_id lines keep the last row per readings-format contract."""
    rows = read_tsv_rows(FIX / "scarlet-base-lot" / "readings.tsv")
    assert len(rows) == 2


def test_t010955_tdl13_correlate_fills_all_rows():
    """correlate subcommand adds delta_e and drift_class to every correlation row."""
    wipe()
    invoke([str(CLI), "ingest-scenario", "--scenario", "scarlet-base-lot", "--run-id", "run-partial"])
    invoke([str(CLI), "correlate", "--run-id", "run-partial"])
    corr_snap = json.loads((CORR_SNAP_DIR / "run-partial.json").read_text())
    for row in corr_snap["rows"]:
        assert "delta_e" in row
        assert "drift_class" in row


def test_t010955_tdl14_export_reads_corr_snap_only():
    """export-report succeeds from correlation snapshot when bundled readings.tsv is emptied."""
    wipe()
    invoke([str(CLI), "ingest-scenario", "--scenario", "scarlet-base-lot", "--run-id", "run-export"])
    invoke([str(CLI), "correlate", "--run-id", "run-export"])
    readings = FIX / "scarlet-base-lot" / "readings.tsv"
    backup = readings.read_text(encoding="utf-8")
    try:
        readings.write_text("batch_id\treading_id\tL\ta\tb\tmeasured_at_epoch\tspectrometer_id\n", encoding="utf-8")
        out = APP / "output" / "run-export-out.json"
        proc = invoke([str(CLI), "export-report", "--run-id", "run-export", "--output", str(out)])
        assert proc.returncode == 0
        rep = json.loads(out.read_text(encoding="utf-8"))
        assert rep["totals"]["row_count"] == 2
    finally:
        readings.write_text(backup, encoding="utf-8")


def test_t010955_tdl15_registry_append_on_ingest():
    """ingest-scenario appends run id and digest to the run registry jsonl path."""
    wipe()
    pipeline("scarlet-base-lot", "run-reg")
    reg_path = APP / "state" / "run-registry.jsonl"
    assert reg_path.is_file()
    reg = reg_path.read_text(encoding="utf-8").strip().splitlines()
    assert any("run-reg" in line for line in reg)


def test_t010955_tdl16_randomized_ephemeral_scenario(tmp_path: Path):
    """Randomized ephemeral fixture rows match reference without hard-coded ids."""
    wipe()
    rng = random.Random(90210)
    batch_id = f"LOT-R{rng.randint(10000, 99999)}"
    reading_id = f"RD-R{rng.randint(1000, 9999)}"
    L = round(rng.uniform(40, 70), 2)
    a = round(rng.uniform(-20, 20), 2)
    b = round(rng.uniform(-30, 30), 2)
    target = (round(L - 1.5, 2), round(a - 0.3, 2), round(b - 0.4, 2))
    root = tmp_path / "rand-root"
    from shadedrift_contract_math import build_ephemeral_scenario

    build_ephemeral_scenario(
        root,
        batch_id=batch_id,
        reading_id=reading_id,
        L=L,
        a=a,
        b=b,
        target=target,
    )
    scenario_dir = root / "ephemeral"
    out = pipeline("ephemeral", "run-rand", scenario_root=root)
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_report(scenario_dir, "run-rand", POLICY)
    assert rep["drift_rows"] == ref["drift_rows"]


def test_t010955_tdl17_correlate_scenario_helper_matches_cli():
    """CLI drift_rows match correlate_scenario helper for indigo rework bundle."""
    policy = json.loads(POLICY.read_text())
    ref_rows = correlate_scenario(FIX / "indigo-rework-window", policy)
    wipe()
    out = pipeline("indigo-rework-window", "run-helper")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert rep["drift_rows"] == ref_rows


def test_t010955_tdl18_report_row_sort_order():
    """export-report drift_rows sort by batch_id then reading_id."""
    wipe()
    out = pipeline("indigo-rework-window", "run-sort")
    rep = json.loads(out.read_text(encoding="utf-8"))
    keys = [(r["batch_id"], r["reading_id"]) for r in rep["drift_rows"]]
    assert keys == sorted(keys)


def test_t010955_tdl19_corr_snap_and_output_paths_exist():
    """Pipeline writes /app/state/shade-correlation/ correlation snapshot and /app/output/ report."""
    wipe()
    out = pipeline("scarlet-base-lot", "run-paths")
    corr_snap = CORR_SNAP_DIR / "run-paths.json"
    assert corr_snap.is_file()
    assert corr_snap.parent == APP / "state" / "shade-correlation"
    assert str(corr_snap.parent) == "/app/state/shade-correlation"
    assert out.parent == APP / "output"
    assert str(out.parent).startswith("/app/output")
    assert out.is_file()


def test_t010955_tdl20_instruction_paths_quoted_in_tests():
    """Quoted /app paths in tests align with instruction output contracts."""
    wipe()
    pipeline("scarlet-base-lot", "run-path-contract")
    registry = "/app/state/run-registry.jsonl"
    corr_snap_root = "/app/state/shade-correlation/"
    output_root = "/app/output/"
    assert (APP / "state" / "run-registry.jsonl").is_file()
    assert str(APP / "state" / "run-registry.jsonl") == registry
    assert str(CORR_SNAP_DIR) + "/" == corr_snap_root
    assert str(APP / "output") + "/" == output_root


def test_t010955_tdl00_subprocess_cli_invocation():
    """CLI is invoked through subprocess in shadedrift_runner."""
    proc = subprocess.run([str(CLI), "ingest-scenario", "--help"], capture_output=True, text=True)
    assert proc.returncode in (0, 2)
    assert "ingest-scenario" in proc.stderr + proc.stdout
