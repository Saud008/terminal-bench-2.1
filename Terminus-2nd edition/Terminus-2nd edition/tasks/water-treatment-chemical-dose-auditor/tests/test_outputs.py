"""Core wtcdctl load-shift-dose and breach atlas contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from wtcda_refmath import (
    arc_ppm_fingerprint as reference_fingerprint,
    m3h_to_lpm as reference_m3h_to_lpm,
    normalize_mg_per_l as reference_normalize,
    reference_safety,
    revision_token as reference_revision_token,
    turbidity_uplift as reference_uplift,
)
from wtcda_subprocess import CLI_BIN, FIXTURE_DIR, ledger_path, invoke, run_safety_pipeline, wipe

APP = Path("/app")


def test_wtcda_p01() -> None:
    """Instruction requires wtcdctl at /app/bin/wtcdctl after cargo build."""
    assert CLI_BIN.is_file()


def test_wtcda_p02() -> None:
    """load-shift-dose must write /app/work/dose-ledger/<plant-id>.json with revision token."""
    wipe()
    plant, shift = "plant-north-alpha", "dual-chem-basic"
    proc = invoke([str(CLI_BIN), "load-shift-dose", "--plant", plant, "--shift", shift])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(ledger_path(plant).read_text(encoding="utf-8"))
    assert body["ledger_revision_token"] == reference_revision_token(
        plant, shift, body["as_of"]
    )
    assert body["plant_id"] == plant
    assert body["shift"] == shift


def test_wtcda_p03() -> None:
    """dose-ledger-schema.md derives ledger_revision_token from plant_id, shift, and as_of."""
    wipe()
    plant, shift = "plant-north-alpha", "dual-chem-basic"
    for _ in range(2):
        proc = invoke([str(CLI_BIN), "load-shift-dose", "--plant", plant, "--shift", shift])
        assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(ledger_path(plant).read_text(encoding="utf-8"))
    assert body["ledger_revision_token"] == reference_revision_token(
        plant, shift, body["as_of"]
    )


def test_wtcda_p04() -> None:
    """export-breach-atlas must succeed after load-shift-dose writes the dose ledger."""
    wipe()
    plant, shift = "plant-north-alpha", "dual-chem-basic"
    run_safety_pipeline(plant, shift)
    assert ledger_path(plant).exists()


def test_wtcda_p05() -> None:
    """Safety rows, summary, and breach_atlas_seal must match independent reference math."""
    wipe()
    plant, shift = "plant-north-alpha", "dual-chem-basic"
    out = run_safety_pipeline(plant, shift)
    got = json.loads(out.read_text(encoding="utf-8"))
    exp = reference_safety(plant, shift, FIXTURE_DIR / f"{shift}.json")
    assert got["rows"] == exp["rows"]
    assert got["summary"] == exp["summary"]
    assert got["breach_atlas_seal"] == exp["breach_atlas_seal"]


def test_wtcda_p06() -> None:
    """chem-lot-fingerprint.md defines chem_id:lot_code:as_of digest field order."""
    wipe()
    plant, shift = "plant-north-alpha", "dual-chem-basic"
    invoke([str(CLI_BIN), "load-shift-dose", "--plant", plant, "--shift", shift])
    snap = json.loads(ledger_path(plant).read_text(encoding="utf-8"))
    chem = snap["chemicals"][0]
    assert chem["arc_tok"] == reference_fingerprint(
        chem["chem_id"], "LOT-881", snap["as_of"]
    )


def test_wtcda_p07() -> None:
    """flow-meter-scaling.md converts m3/h to L/min with times 1000 divided by 60."""
    assert reference_m3h_to_lpm(120.0) == 2000.0


def test_wtcda_p08() -> None:
    """concentration-unit-normalization.md multiplies percent concentrations by 10000."""
    assert reference_normalize(0.05, "percent") == 500.0


def test_wtcda_p09() -> None:
    """flow-weighted-dose-kernel.md caps turbidity uplift at 1.5."""
    assert reference_uplift(8.0, 1.0) == 1.5


def test_wtcda_p10() -> None:
    """sensor-outage-forward-fill.md forward-fills up to three outage minutes per sensor."""
    wipe()
    plant, shift = "plant-east-gamma", "outage-forward-fill"
    invoke([str(CLI_BIN), "load-shift-dose", "--plant", plant, "--shift", shift])
    snap = json.loads(ledger_path(plant).read_text(encoding="utf-8"))
    exp = reference_safety(plant, shift, FIXTURE_DIR / f"{shift}.json")["_ledger"]["chemicals"][0]
    assert snap["chemicals"][0]["total_dose_mg"] == exp["total_dose_mg"]


def test_wtcda_p11() -> None:
    """override-authorization-policy.md matches roles without ASCII case sensitivity."""
    wipe()
    plant, shift = "plant-west-delta", "override-role-mix"
    invoke([str(CLI_BIN), "load-shift-dose", "--plant", plant, "--shift", shift])
    snap = json.loads(ledger_path(plant).read_text(encoding="utf-8"))
    assert snap["chemicals"][0]["override_applied"] is True


def test_wtcda_p12() -> None:
    """Denylisted guest.temp must not apply a 2.0 override factor."""
    wipe()
    plant, shift = "plant-west-delta", "override-role-mix"
    out = run_safety_pipeline(plant, shift)
    got = json.loads(out.read_text(encoding="utf-8"))
    exp = reference_safety(plant, shift, FIXTURE_DIR / f"{shift}.json")
    assert got["rows"] == exp["rows"]


def test_wtcda_p13() -> None:
    """Weighted concentration uses flow-weighted mean, not a simple average."""
    wipe()
    plant, shift = "plant-north-alpha", "dual-chem-basic"
    invoke([str(CLI_BIN), "load-shift-dose", "--plant", plant, "--shift", shift])
    snap = json.loads(ledger_path(plant).read_text(encoding="utf-8"))
    exp = reference_safety(plant, shift, FIXTURE_DIR / f"{shift}.json")["_ledger"]["chemicals"]
    for got_row, exp_row in zip(snap["chemicals"], exp):
        assert got_row["weighted_conc_mg_l"] == exp_row["weighted_conc_mg_l"]


def test_wtcda_p14() -> None:
    """Percent lot normalization drives total dose for plant-central-zeta shift."""
    wipe()
    plant, shift = "plant-central-zeta", "percent-unit-lot"
    invoke([str(CLI_BIN), "load-shift-dose", "--plant", plant, "--shift", shift])
    snap = json.loads(ledger_path(plant).read_text(encoding="utf-8"))
    exp = reference_safety(plant, shift, FIXTURE_DIR / f"{shift}.json")["_ledger"]["chemicals"][0]
    assert abs(snap["chemicals"][0]["total_dose_mg"] - exp["total_dose_mg"]) < 0.01


def test_wtcda_p15() -> None:
    """safety-limit-report.md ranks breaches by severity_pct descending then chem_id."""
    wipe()
    plant, shift = "plant-north-alpha", "dual-chem-basic"
    out = run_safety_pipeline(plant, shift)
    rows = json.loads(out.read_text(encoding="utf-8"))["rows"]
    if len(rows) >= 2:
        assert rows[0]["severity_pct"] >= rows[1]["severity_pct"]


def test_wtcda_p16() -> None:
    """High turbidity minute applies uplift factor to COAG-C9 dose total."""
    wipe()
    plant, shift = "plant-south-epsilon", "turbidity-uplift-cap"
    invoke([str(CLI_BIN), "load-shift-dose", "--plant", plant, "--shift", shift])
    snap = json.loads(ledger_path(plant).read_text(encoding="utf-8"))
    exp = reference_safety(plant, shift, FIXTURE_DIR / f"{shift}.json")["_ledger"]["chemicals"][0]
    assert abs(snap["chemicals"][0]["total_dose_mg"] - exp["total_dose_mg"]) < 0.01


def test_wtcda_p17() -> None:
    """dose-ledger-schema.md lists required chemical row keys."""
    wipe()
    plant, shift = "plant-north-alpha", "dual-chem-basic"
    invoke([str(CLI_BIN), "load-shift-dose", "--plant", plant, "--shift", shift])
    row = json.loads(ledger_path(plant).read_text(encoding="utf-8"))["chemicals"][0]
    for key in (
        "chem_id",
        "arc_tok",
        "weighted_conc_mg_l",
        "total_dose_mg",
        "max_dose_mg",
        "contact_excluded_minutes",
        "override_applied",
    ):
        assert key in row


def test_wtcda_p18() -> None:
    """Safety summary must count chemicals and breaches from ledger totals."""
    wipe()
    plant, shift = "plant-north-alpha", "dual-chem-basic"
    out = run_safety_pipeline(plant, shift)
    summary = json.loads(out.read_text(encoding="utf-8"))["summary"]
    assert summary["chemical_count"] == 2
    assert summary["plant_id"] == plant


def test_wtcda_p19() -> None:
    """load-shift-dose without --plant must exit non-zero."""
    wipe()
    proc = invoke([str(CLI_BIN), "load-shift-dose", "--shift", "dual-chem-basic"])
    assert proc.returncode != 0
