"""skew-cal CLI surface and workspace hygiene checks."""

from __future__ import annotations

import json

from conftest import APP_ROOT, SKEW_CAL_BIN


def test_release_binary_installed():
    """skew-cal release binary must exist at /app/bin/skew-cal per instruction."""
    assert SKEW_CAL_BIN.is_file()


def test_fixture_catalog_lists_four_rover_bags(c8skew):
    """Bundled bag_catalog.json lists at least four rover field logs."""
    catalog = json.loads((APP_ROOT / "fixtures" / "bag_catalog.json").read_text(encoding="utf-8"))
    assert len(catalog["bags"]) >= 4
    ids = {entry["bag_id"] for entry in catalog["bags"]}
    assert "rover-alpha" in ids


def test_skew_atlas_output_suffix(c8skew):
    """emit-skew writes filenames ending with -skew-atlas.json."""
    out = c8skew.run_skew_pipeline("rover-alpha")
    assert out.name.endswith("-skew-atlas.json")


def test_tf_decoy_not_on_cli_help(c8skew):
    """tf extrapolation decoy is not advertised by skew-cal usage text."""
    proc = c8skew.shell([str(SKEW_CAL_BIN)])
    assert proc.returncode != 0
    combined = (proc.stderr + proc.stdout).lower()
    assert "tf" not in combined or "usage" in proc.stderr


def test_reset_script_clears_manifest_revision(c8skew):
    """reset-workspace.sh restores manifest_revision to one on a fresh latch."""
    bag_id = "rover-alpha"
    c8skew.run_skew_pipeline(bag_id)
    c8skew.reset_workspace()
    bdir = c8skew.bag_path(bag_id)
    c8skew.shell(
        [
            str(SKEW_CAL_BIN),
            "latch-meta",
            "--bag-id",
            bag_id,
            "--meta",
            str(bdir / "bag_meta.json"),
        ]
    )
    latch_doc = c8skew.read_manifest_latch(bag_id)
    assert latch_doc["manifest_revision"] == 1
