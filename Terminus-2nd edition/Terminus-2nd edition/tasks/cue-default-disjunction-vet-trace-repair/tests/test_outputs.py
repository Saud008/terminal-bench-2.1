"""Behavioral verifier for cuectl vet/export CLI."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
VERIFIER_LIB = TESTS / "verifier-lib"
GOLDEN_DIR = TESTS / "verifier-golden"
sys.path.insert(0, str(VERIFIER_LIB))
from reference_cue import (  # noqa: E402
    build_eval_snapshot,
    default_disjunct_index,
    eval_snapshot_path,
    reference_export,
    reference_vet,
    resolve_disjunct_value,
    trace_by_path,
)

APP = Path("/app")
CLI = "/usr/local/bin/cuectl"
WORKSPACES = APP / "workspaces"
OUTPUT = APP / "output"
FIXTURES = APP / "fixtures"
CATALOG = json.loads((FIXTURES / "catalog.json").read_text(encoding="utf-8"))
SEEDS = json.loads((FIXTURES / "seeds.json").read_text(encoding="utf-8"))["seeds"]
RESET = APP / "scripts" / "reset-state.sh"
CUEWRAP = APP / "internal" / "cuewrap"
BROKEN_SNAPSHOT = Path("/opt/verifier-broken-cuewrap")
HIDDEN_TWIN = Path("/opt/verifier-fixtures/workspaces/ws-twin")
MODULES = (
    "disjunct",
    "closed",
    "embed",
    "compose",
    "snapshot_bind",
    "snapshot_guard",
    "diag_linefmt",
    "vet",
    "export",
)
EVAL_SNAPSHOTS = APP / "state" / "eval-snapshots"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def go_rebuild_install() -> None:
    proc = run(["go", "build", "-o", CLI, "./cmd/cuectl"])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def install_modules(golden_dir: Path, only_broken: set[str]) -> None:
    for mod in MODULES:
        dest = CUEWRAP / f"{mod}.go"
        if mod in only_broken:
            shutil.copy2(BROKEN_SNAPSHOT / f"{mod}.go", dest)
        else:
            shutil.copy2(golden_dir / f"golden_{mod}.go", dest)
        dest.touch()


@contextmanager
def with_module_patch(only_broken: set[str]):
    """Swap cuewrap modules for partial-golden probes; restore agent tree after."""
    saved = {
        mod: (CUEWRAP / f"{mod}.go").read_text(encoding="utf-8") for mod in MODULES
    }
    try:
        install_modules(GOLDEN_DIR, only_broken)
        go_rebuild_install()
        yield
    finally:
        for mod, content in saved.items():
            (CUEWRAP / f"{mod}.go").write_text(content, encoding="utf-8")
        go_rebuild_install()


@pytest.fixture(scope="session", autouse=True)
def _verifier_golden_present() -> None:
    assert (GOLDEN_DIR / "golden_disjunct.go").is_file(), (
        f"verifier golden modules missing under {GOLDEN_DIR}"
    )


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def workspace_dir(name: str) -> Path:
    entry = next(item for item in CATALOG["workspaces"] if item["name"] == name)
    return WORKSPACES / entry["dir"]


def cuectl_vet(ws_name: str, seed: str) -> tuple[subprocess.CompletedProcess[str], Path]:
    out = OUTPUT / f"vet-{ws_name}-{seed}.json"
    proc = run(
        [
            CLI,
            "vet",
            "--workspace",
            str(workspace_dir(ws_name)),
            "--seed",
            seed,
            "--export",
            str(out),
        ]
    )
    return proc, out


def cuectl_export(ws_name: str, seed: str) -> tuple[subprocess.CompletedProcess[str], Path]:
    out = OUTPUT / f"export-{ws_name}-{seed}.json"
    proc = run(
        [
            CLI,
            "export",
            "--workspace",
            str(workspace_dir(ws_name)),
            "--seed",
            seed,
            "--export",
            str(out),
        ]
    )
    return proc, out


def cuectl_export_dir(
    ws_dir: Path, ws_name: str, seed: str
) -> tuple[subprocess.CompletedProcess[str], Path]:
    out = OUTPUT / f"export-{ws_name}-{seed}.json"
    proc = run(
        [
            CLI,
            "export",
            "--workspace",
            str(ws_dir),
            "--seed",
            seed,
            "--export",
            str(out),
        ]
    )
    return proc, out


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_closed_unknown_field_error(error: str, field: str = "shadow") -> None:
    """Medium check: closed vet failures must name closed semantics and the unknown field."""
    lower = error.lower()
    assert "closed" in lower, error
    assert field.lower() in lower, error


def assert_default_disjunct_detail(detail: str, opts: list[str]) -> None:
    """Medium check: default disjunct traces must mention default/disjunct and every option."""
    lower = detail.lower()
    assert "default" in lower or "disjunct" in lower, detail
    for opt in opts:
        assert opt in detail, detail


def assert_lineage_covers_field(lineage: list[str], cfg_id: str, field: str) -> None:
    """Medium check: lineage starts at config root and ends at the field leaf."""
    assert lineage[0] == f"config.{cfg_id}", lineage
    assert lineage[-1] == field, lineage
    assert len(lineage) >= 3, lineage


def assert_vet_traces_cover_paths(got: dict, expected: dict, paths: list[str]) -> None:
    """Medium spot-check: compare ok and per-path shape without full trace-doc equality."""
    assert got["ok"] == expected["ok"]
    if not expected["ok"]:
        return
    for path in paths:
        trace = trace_by_path(got, path)
        ref = trace_by_path(expected, path)
        assert trace["path"] == ref["path"] == path
        assert trace["attr"] == ref["attr"]
        cfg_id = path.split(".")[1]
        field = path.split(".")[-1]
        assert_lineage_covers_field(trace["lineage"], cfg_id, field)
        if ref["attr"] == "default":
            match = re.search(r"\[(.+)\]", ref["detail"])
            assert match is not None, ref["detail"]
            assert_default_disjunct_detail(trace["detail"], match.group(1).split())


@pytest.fixture(autouse=True)
def _reset_env() -> None:
    reset()


@pytest.mark.parametrize("seed", ["alpha01", "beta17"])
def test_t6e7977_lattice_vet_default_trace_medium(seed: str) -> None:
    """Default disjunct vet traces must identify path, default attr, options, and config root."""
    proc, out = cuectl_vet("ws-lattice", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(out)
    expected = reference_vet(workspace_dir("ws-lattice"), seed)
    assert got["ok"] is True
    trace = trace_by_path(got, "config.app.size")
    ref = trace_by_path(expected, "config.app.size")
    assert trace["path"] == ref["path"] == "config.app.size"
    assert trace["attr"] == "default"
    assert_lineage_covers_field(trace["lineage"], "app", "size")
    assert trace["detail"] == ref["detail"]
    assert_default_disjunct_detail(trace["detail"], ["small", "large"])


@pytest.mark.parametrize("seed", SEEDS)
def test_t6e7977_lattice_export_disjunct_value_seed_flipped(seed: str) -> None:
    """Bare disjunct fields must resolve via fnv1a64(seed) % count, not a fixed index."""
    proc, out = cuectl_export("ws-lattice", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(out)
    expected = reference_export(workspace_dir("ws-lattice"), seed)
    path = "config.app.size"
    assert got["values"][path] == expected["values"][path]
    assert got["values"][path] == resolve_disjunct_value(seed, ["small", "large"])


def test_t6e7977_lattice_seed_flip_not_always_first_option() -> None:
    """At least one catalog seed must pick the non-zero disjunct index."""
    values = {seed: resolve_disjunct_value(seed, ["small", "large"]) for seed in SEEDS}
    assert "large" in values.values()
    assert default_disjunct_index("beta17", 2) == 1


def test_t6e7977_guard_vet_rejects_closed_unknown_field() -> None:
    """Closed schemas must fail vet when configs introduce unknown fields."""
    proc, out = cuectl_vet("ws-guard", SEEDS[0])
    assert proc.returncode == 1, proc.stderr or proc.stdout
    got = load_json(out)
    expected = reference_vet(workspace_dir("ws-guard"), SEEDS[0])
    assert got["ok"] is False
    assert expected["ok"] is False
    assert_closed_unknown_field_error(got["error"])
    assert "closed schema rejects field shadow" in got["error"]
    assert "phantom" not in got["error"]


def test_t6e7977_lineage_vet_trace_schema_hops() -> None:
    """Embed lineage traces must list config root, schema chain, then field leaf."""
    proc, out = cuectl_vet("ws-lineage", SEEDS[0])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(out)
    expected = reference_vet(workspace_dir("ws-lineage"), SEEDS[0])
    trace = trace_by_path(got, "config.app.flag")
    ref = trace_by_path(expected, "config.app.flag")
    assert trace["lineage"] == ref["lineage"]
    assert trace["path"] == ref["path"] == "config.app.flag"
    assert trace["attr"] == "lineage"


def test_t6e7977_cycle_vet_fails_with_embed_cycle_error() -> None:
    """Circular embed chains must fail vet with an embed cycle error."""
    proc, out = cuectl_vet("ws-cycle", SEEDS[0])
    assert proc.returncode == 1, proc.stderr or proc.stdout
    got = load_json(out)
    expected = reference_vet(workspace_dir("ws-cycle"), SEEDS[0])
    assert got["ok"] is False
    assert expected["ok"] is False
    assert "embed cycle" in got["error"]


def test_t6e7977_cycle_export_fails_with_embed_cycle_error() -> None:
    """Circular embed chains must fail export when cycle detection is enforced."""
    proc, _ = cuectl_export("ws-cycle", SEEDS[0])
    assert proc.returncode == 1, proc.stderr or proc.stdout
    with pytest.raises(ValueError, match="embed cycle"):
        reference_export(workspace_dir("ws-cycle"), SEEDS[0])


def test_t6e7977_provenance_export_optional_rows() -> None:
    """Export must emit provenance rows for every optional export rule."""
    proc, out = cuectl_export("ws-provenance", SEEDS[0])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(out)
    expected = reference_export(workspace_dir("ws-provenance"), SEEDS[0])
    assert got["provenance"] == expected["provenance"]
    assert len(got["provenance"]) == 1


def test_t6e7977_merged_vet_traces_lineage_and_default() -> None:
    """Merged workspace vet must expose lineage roots and leaves for tier and flag."""
    seed = SEEDS[2]
    proc, out = cuectl_vet("ws-merged", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(out)
    assert got["ok"] is True
    tier = trace_by_path(got, "config.app.tier")
    flag = trace_by_path(got, "config.app.flag")
    assert_lineage_covers_field(tier["lineage"], "app", "tier")
    assert_lineage_covers_field(flag["lineage"], "app", "flag")
    assert "Profile" in tier["lineage"]
    assert tier["attr"] == "default"
    assert flag["attr"] == "lineage"
    expected = reference_vet(workspace_dir("ws-merged"), seed)
    ref_tier = trace_by_path(expected, "config.app.tier")
    assert tier["detail"] == ref_tier["detail"]
    assert_default_disjunct_detail(tier["detail"], ["east", "west"])


def test_t6e7977_merged_export_provenance_and_disjunct(seed: str = SEEDS[1]) -> None:
    """Merged export must include optional provenance and seed-based tier disjunct."""
    proc, out = cuectl_export("ws-merged", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(out)
    expected = reference_export(workspace_dir("ws-merged"), seed)
    assert got["values"]["config.app.tier"] == expected["values"]["config.app.tier"]
    assert got["provenance"] == expected["provenance"]
    assert got["provenance"][0]["path"] == "config.app.tag"


@pytest.mark.parametrize("seed", SEEDS)
def test_t6e7977_trifold_export_disjunct_value_seed_flipped(seed: str) -> None:
    """Triple-option disjunct fields must resolve via fnv1a64(seed) % 3."""
    proc, out = cuectl_export("ws-trifold", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(out)
    expected = reference_export(workspace_dir("ws-trifold"), seed)
    path = "config.run.choice"
    assert got["values"][path] == expected["values"][path]
    assert got["values"][path] == resolve_disjunct_value(seed, ["alpha", "beta", "gamma"])


def test_t6e7977_trifold_seed_flip_covers_nonzero_indices() -> None:
    """At least one catalog seed must pick each non-zero triple-disjunct index."""
    values = {
        seed: resolve_disjunct_value(seed, ["alpha", "beta", "gamma"]) for seed in SEEDS
    }
    assert "beta" in values.values()
    assert "gamma" in values.values()
    assert default_disjunct_index("alpha01", 3) == 2
    assert default_disjunct_index("delta42", 3) == 1


@pytest.mark.parametrize("seed", ["alpha01", "beta17"])
def test_t6e7977_trifold_vet_default_trace_three_options(seed: str) -> None:
    """Triple disjunct vet traces must list all three default options."""
    proc, out = cuectl_vet("ws-trifold", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(out)
    expected = reference_vet(workspace_dir("ws-trifold"), seed)
    assert got["ok"] is True
    trace = trace_by_path(got, "config.run.choice")
    ref = trace_by_path(expected, "config.run.choice")
    assert trace["path"] == ref["path"] == "config.run.choice"
    assert trace["attr"] == "default"
    assert trace["detail"] == ref["detail"]
    assert_default_disjunct_detail(trace["detail"], ["alpha", "beta", "gamma"])


def test_t6e7977_deep_embed_lineage_transitive_field() -> None:
    """Three-level embed chains must expose full schema hops through grandparents."""
    seed = SEEDS[0]
    proc, out = cuectl_vet("ws-deep", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(out)
    expected = reference_vet(workspace_dir("ws-deep"), seed)
    rev = trace_by_path(got, "config.app.rev")
    flag = trace_by_path(got, "config.app.flag")
    ref_rev = trace_by_path(expected, "config.app.rev")
    ref_flag = trace_by_path(expected, "config.app.flag")
    assert rev["lineage"] == ref_rev["lineage"] == [
        "config.app",
        "App",
        "Base",
        "Core",
        "rev",
    ]
    assert flag["lineage"] == ref_flag["lineage"] == [
        "config.app",
        "App",
        "Base",
        "Core",
        "flag",
    ]
    assert rev["attr"] == flag["attr"] == "lineage"


def test_t6e7977_deep_export_includes_transitive_rev() -> None:
    """Transitive embed fields from grandparent schemas must appear in export values."""
    seed = SEEDS[1]
    proc, out = cuectl_export("ws-deep", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(out)
    expected = reference_export(workspace_dir("ws-deep"), seed)
    assert got["values"] == expected["values"]
    assert got["values"]["config.app.rev"] == 42
    assert got["values"]["config.app.flag"] == "on"
    assert got["values"]["config.app.mode"] == "live"


@pytest.mark.parametrize(
    ("ws_name", "seed"),
    [
        ("ws-lattice", "alpha01"),
        ("ws-lattice", "beta17"),
        ("ws-merged", "epoch07"),
        ("ws-provenance", "gamma99"),
        ("ws-deep", "delta42"),
        ("ws-trifold", "epoch07"),
    ],
)
def test_t6e7977_eval_snapshot_written(ws_name: str, seed: str) -> None:
    """Stage 1 must persist eval snapshots before vet/export output is written."""
    proc, _ = cuectl_export(ws_name, seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    snap_path = eval_snapshot_path(ws_name, seed)
    assert snap_path.is_file(), f"missing eval snapshot: {snap_path}"


@pytest.mark.parametrize(
    ("ws_name", "seed"),
    [
        ("ws-lattice", "delta42"),
        ("ws-merged", "beta17"),
        ("ws-guard", SEEDS[0]),
        ("ws-cycle", SEEDS[0]),
        ("ws-deep", "gamma99"),
        ("ws-trifold", "delta42"),
    ],
)
def test_t6e7977_eval_snapshot_matches_reference(ws_name: str, seed: str) -> None:
    """Eval snapshot JSON must match the independent reference compose builder."""
    expect_rc = 0 if ws_name not in ("ws-guard", "ws-cycle") else 1
    proc, _ = cuectl_vet(ws_name, seed) if ws_name in ("ws-guard", "ws-cycle") else cuectl_export(ws_name, seed)
    assert proc.returncode == expect_rc, proc.stderr or proc.stdout
    snap_path = eval_snapshot_path(ws_name, seed)
    if ws_name in ("ws-guard", "ws-cycle"):
        assert snap_path.is_file(), f"missing eval snapshot for failure case: {snap_path}"
    actual = load_json(snap_path)
    expected = build_eval_snapshot(workspace_dir(ws_name), seed)
    assert actual["version"] == expected["version"] == 1
    assert actual["workspace"] == expected["workspace"] == ws_name
    assert actual["seed"] == expected["seed"] == seed
    assert actual["ok"] == expected["ok"]
    if expected["ok"]:
        assert actual["values"] == expected["values"]
    else:
        assert "error" in actual
        assert expected["error"] in actual["error"] or actual["error"] in expected["error"]


def test_t6e7977_export_reads_snapshot_not_rerun_disjunct() -> None:
    """Golden compose/export must surface broken disjunct values from the eval snapshot."""
    with with_module_patch({"disjunct"}):
        proc, out = cuectl_export("ws-lattice", "beta17")
        assert proc.returncode == 0
        got = load_json(out)
        expected = reference_export(workspace_dir("ws-lattice"), "beta17")
        assert got["values"]["config.app.size"] != expected["values"]["config.app.size"]
        snap = load_json(eval_snapshot_path("ws-lattice", "beta17"))
        assert snap["values"]["config.app.size"] == got["values"]["config.app.size"]


@pytest.mark.parametrize(
    ("ws_name", "seed", "expect_rc", "trace_paths"),
    [
        ("ws-lattice", "delta42", 0, ["config.app.size"]),
        ("ws-merged", "epoch07", 0, ["config.app.tier", "config.app.flag"]),
        ("ws-provenance", "gamma99", 0, []),
        ("ws-guard", SEEDS[0], 1, []),
        ("ws-cycle", SEEDS[0], 1, []),
        ("ws-deep", "delta42", 0, ["config.app.rev", "config.app.flag"]),
        ("ws-trifold", "gamma99", 0, ["config.run.choice"]),
    ],
)
def test_t6e7977_spot_check_vet_matches_reference(
    ws_name: str, seed: str, expect_rc: int, trace_paths: list[str]
) -> None:
    """Spot-check vet JSON against the independent reference implementation."""
    proc, out = cuectl_vet(ws_name, seed)
    assert proc.returncode == expect_rc, proc.stderr or proc.stdout
    got = load_json(out)
    expected = reference_vet(workspace_dir(ws_name), seed)
    assert got["ok"] == expected["ok"]
    if trace_paths:
        assert_vet_traces_cover_paths(got, expected, trace_paths)


def test_t6e7977_failed_snapshot_omits_values() -> None:
    """Failed eval snapshots must not include a values object."""
    proc, _ = cuectl_vet("ws-guard", SEEDS[0])
    assert proc.returncode == 1, proc.stderr or proc.stdout
    snap_path = eval_snapshot_path("ws-guard", SEEDS[0])
    assert snap_path.is_file(), f"missing eval snapshot: {snap_path}"
    snap = load_json(snap_path)
    assert snap["ok"] is False
    assert "values" not in snap
    assert "closed schema rejects field shadow" in snap["error"]


def test_t6e7977_tampered_snapshot_recomposed_on_export() -> None:
    """Stage 1 must recompose when an on-disk eval snapshot values were tampered."""
    ws_name = "ws-lattice"
    seed = "alpha01"
    proc, _ = cuectl_export(ws_name, seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    snap_path = eval_snapshot_path(ws_name, seed)
    snap = load_json(snap_path)
    snap["values"]["config.app.size"] = "large"
    snap_path.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
    proc2, out2 = cuectl_export(ws_name, seed)
    assert proc2.returncode == 0, proc2.stderr or proc2.stdout
    got = load_json(out2)
    expected = reference_export(workspace_dir(ws_name), seed)
    assert got["values"]["config.app.size"] == expected["values"]["config.app.size"]
    assert got["values"]["config.app.size"] == resolve_disjunct_value(seed, ["small", "large"])


def test_t6e7977_hidden_twin_dual_disjunct_export() -> None:
    """Hidden /opt/verifier-fixtures ws-twin must resolve both disjunct fields from the seed hash."""
    assert HIDDEN_TWIN.is_dir(), "hidden ws-twin fixture not mounted"
    seed = "epoch07"
    proc, out = cuectl_export_dir(HIDDEN_TWIN, "ws-twin", seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(out)
    expected = reference_export(HIDDEN_TWIN, seed)
    assert got["values"]["config.run.lane"] == expected["values"]["config.run.lane"]
    assert got["values"]["config.run.tier"] == expected["values"]["config.run.tier"]
    assert got["values"]["config.run.lane"] == resolve_disjunct_value(seed, ["east", "west"])
    assert got["values"]["config.run.tier"] == resolve_disjunct_value(seed, ["low", "high"])
    assert len(got["provenance"]) == 2


def test_t6e7977_hidden_twin_vet_default_traces() -> None:
    """Hidden /opt/verifier-fixtures ws-twin vet must list both default disjunct traces."""
    assert HIDDEN_TWIN.is_dir(), "hidden ws-twin fixture not mounted"
    seed = "beta17"
    out = OUTPUT / f"vet-ws-twin-{seed}.json"
    proc = run(
        [
            CLI,
            "vet",
            "--workspace",
            str(HIDDEN_TWIN),
            "--seed",
            seed,
            "--export",
            str(out),
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = load_json(out)
    expected = reference_vet(HIDDEN_TWIN, seed)
    assert got["ok"] is True
    assert_vet_traces_cover_paths(
        got, expected, ["config.run.lane", "config.run.tier"]
    )


def test_t6e7977_partial_broken_compose_leaks_values_without_guard() -> None:
    """Golden modules except compose/guard still write partial values on closed failure."""
    with with_module_patch({"compose", "snapshot_guard"}):
        proc, _ = cuectl_vet("ws-guard", SEEDS[0])
        assert proc.returncode == 1, proc.stderr or proc.stdout
        snap = load_json(eval_snapshot_path("ws-guard", SEEDS[0]))
        assert snap["ok"] is False
        assert "values" in snap and len(snap["values"]) > 0


def test_t6e7977_partial_golden_guard_rejects_compose_value_leak() -> None:
    """Golden guard must reject failed snapshots that leak resolved values."""
    with with_module_patch({"compose"}):
        proc, _ = cuectl_vet("ws-guard", SEEDS[0])
        assert proc.returncode != 0, proc.stderr or proc.stdout


def test_t6e7977_partial_broken_vet_wrong_default_detail() -> None:
    """Golden disjunct/closed/embed/compose/guard/export cannot hide wrong default detail format."""
    with with_module_patch({"vet"}):
        proc, out = cuectl_vet("ws-lattice", "alpha01")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = load_json(out)
        expected = reference_vet(workspace_dir("ws-lattice"), "alpha01")
        assert trace_by_path(got, "config.app.size")["detail"] != trace_by_path(
            expected, "config.app.size"
        )["detail"]


def test_t6e7977_partial_broken_snapshot_guard_noop_leaks_values() -> None:
    """Broken guard cannot reject failed snapshots that leak resolved values."""
    with with_module_patch({"compose", "snapshot_guard"}):
        proc, _ = cuectl_vet("ws-guard", SEEDS[0])
        assert proc.returncode == 1, proc.stderr or proc.stdout
        snap = load_json(eval_snapshot_path("ws-guard", SEEDS[0]))
        assert snap["ok"] is False
        assert "values" in snap and len(snap["values"]) > 0


def test_t6e7977_partial_broken_disjunct_fails_lattice() -> None:
    """Golden closed/embed/compose/vet/export cannot hide a broken disjunct default picker."""
    with with_module_patch({"disjunct"}):
        proc, out = cuectl_export("ws-lattice", "beta17")
        assert proc.returncode == 0
        got = load_json(out)
        expected = reference_export(workspace_dir("ws-lattice"), "beta17")
        assert got["values"]["config.app.size"] != expected["values"]["config.app.size"]


def test_t6e7977_partial_broken_closed_fails_guard() -> None:
    """Golden disjunct/embed cannot hide broken closed schema enforcement."""
    with with_module_patch({"closed"}):
        proc, out = cuectl_vet("ws-guard", SEEDS[0])
        assert proc.returncode == 1, proc.stderr or proc.stdout
        got = load_json(out)
        assert got["ok"] is False
        assert "phantom" in got["error"]


def test_t6e7977_partial_broken_embed_fails_lineage() -> None:
    """Golden disjunct/closed cannot hide broken embed lineage ordering."""
    with with_module_patch({"embed"}):
        proc, out = cuectl_vet("ws-lineage", SEEDS[0])
        assert proc.returncode == 0
        got = load_json(out)
        expected = reference_vet(workspace_dir("ws-lineage"), SEEDS[0])
        trace = trace_by_path(got, "config.app.flag")
        ref = trace_by_path(expected, "config.app.flag")
        assert trace["lineage"] != ref["lineage"]


def test_t6e7977_partial_broken_embed_fails_cycle() -> None:
    """Golden disjunct/closed/compose/export cannot hide broken embed cycle detection."""
    with with_module_patch({"embed"}):
        proc, out = cuectl_vet("ws-cycle", SEEDS[0])
        got = load_json(out)
        expected = reference_vet(workspace_dir("ws-cycle"), SEEDS[0])
        assert proc.returncode == 0
        assert got["ok"] is True
        assert expected["ok"] is False


def test_t6e7977_partial_broken_export_fails_provenance() -> None:
    """Golden disjunct/closed/embed/compose cannot hide missing export provenance rows."""
    with with_module_patch({"export"}):
        proc, out = cuectl_export("ws-provenance", SEEDS[0])
        assert proc.returncode == 0
        got = load_json(out)
        assert got["provenance"] == []


def test_t6e7977_partial_broken_compose_fails_export_snapshot() -> None:
    """Golden export cannot succeed when compose leaks values on closed-schema failure."""
    with with_module_patch({"compose", "snapshot_guard"}):
        proc, _ = cuectl_export("ws-guard", SEEDS[0])
        assert proc.returncode != 0, proc.stderr or proc.stdout
        snap = load_json(eval_snapshot_path("ws-guard", SEEDS[0]))
        assert snap["ok"] is False
        assert "values" in snap and len(snap["values"]) > 0


def test_t6e7977_partial_broken_embed_fails_deep() -> None:
    """Golden disjunct/closed cannot hide single-level embed flatten on a three-hop chain."""
    with with_module_patch({"embed"}):
        proc, out = cuectl_export("ws-deep", SEEDS[0])
        assert proc.returncode == 0
        got = load_json(out)
        expected = reference_export(workspace_dir("ws-deep"), SEEDS[0])
        assert got["values"].get("config.app.rev") != expected["values"]["config.app.rev"]


def test_t6e7977_partial_broken_disjunct_fails_trifold() -> None:
    """Golden closed/embed/compose/vet/export cannot hide broken triple-disjunct picker."""
    with with_module_patch({"disjunct"}):
        proc, out = cuectl_export("ws-trifold", "delta42")
        assert proc.returncode == 0
        got = load_json(out)
        expected = reference_export(workspace_dir("ws-trifold"), "delta42")
        assert got["values"]["config.run.choice"] != expected["values"]["config.run.choice"]


def test_t6e7977_partial_broken_vet_skips_compose_snapshot() -> None:
    """Golden compose/export cannot hide a vet path that skips stage-1 snapshot writes."""
    with with_module_patch({"vet"}):
        reset()
        proc, _ = cuectl_vet("ws-lattice", "alpha01")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        assert not eval_snapshot_path("ws-lattice", "alpha01").is_file()


def test_t6e7977_partial_broken_snapshot_bind_keeps_tampered_values() -> None:
    """Golden compose/bind pair must not serve tampered snapshot values without recompose."""
    with with_module_patch({"snapshot_bind", "compose"}):
        ws_name = "ws-lattice"
        seed = "alpha01"
        proc, _ = cuectl_export(ws_name, seed)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        snap_path = eval_snapshot_path(ws_name, seed)
        snap = load_json(snap_path)
        snap["values"]["config.app.size"] = "large"
        snap_path.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
        proc2, out2 = cuectl_export(ws_name, seed)
        assert proc2.returncode == 0, proc2.stderr or proc2.stdout
        got = load_json(out2)
        expected = reference_export(workspace_dir(ws_name), seed)
        assert got["values"]["config.app.size"] != expected["values"]["config.app.size"]


def test_t6e7977_partial_broken_closed_picks_alphabetical_unknown() -> None:
    """Golden disjunct/embed cannot hide closed unknown-field ordering bugs."""
    with with_module_patch({"closed"}):
        proc, out = cuectl_vet("ws-guard", SEEDS[0])
        assert proc.returncode == 1, proc.stderr or proc.stdout
        got = load_json(out)
        assert "phantom" in got["error"]


def test_t6e7977_partial_golden_tracefmt_without_vet_still_wrong() -> None:
    """Golden tracefmt alone cannot fix broken vet default detail formatting."""
    with with_module_patch({"vet"}):
        proc, out = cuectl_vet("ws-lattice", "alpha01")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        got = load_json(out)
        expected = reference_vet(workspace_dir("ws-lattice"), "alpha01")
        assert trace_by_path(got, "config.app.size")["detail"] != trace_by_path(
            expected, "config.app.size"
        )["detail"]
