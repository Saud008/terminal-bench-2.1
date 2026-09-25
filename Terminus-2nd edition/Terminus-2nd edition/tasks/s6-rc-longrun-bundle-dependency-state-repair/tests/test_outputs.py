"""Verifier for s6-rc-longrun-bundle-dependency-state-repair (single-step)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from reference_s6rc import (
    all_edges,
    build_ingest,
    find_cycle,
    load_json,
    ready_map,
    run_apply,
    run_export,
    run_ingest,
    run_plan,
    run_ready,
    run_validate,
    topo_plan,
    write_rc,
)

CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text(encoding="utf-8"))
STACK = Path(CATALOG["stack_tree"])
CYCLE = Path(CATALOG["cycle_tree"])
SOFT = Path(CATALOG["soft_tree"])
STACK_BUNDLE = CATALOG["stack_bundle"]
CYCLE_BUNDLE = CATALOG["cycle_bundle"]
SOFT_BUNDLE = CATALOG["soft_bundle"]
STATE = Path("/app/state/rc")
SEED = os.environ.get("VERIFIER_SEED", "s6-rc-longrun-bundle-dependency-state-repair")


@pytest.fixture(autouse=True)
def reset_touch_and_state() -> None:
    touch = Path("/app/output/.parser-touch")
    touch.parent.mkdir(parents=True, exist_ok=True)
    touch.write_text("", encoding="utf-8")
    for path in (
        Path("/app/state/staging.json"),
        Path("/app/state/applied.json"),
        Path("/app/state/transition-log.json"),
        STATE / "services.json",
    ):
        path.unlink(missing_ok=True)
    STATE.mkdir(parents=True, exist_ok=True)
    write_rc(STATE, {})


class TestIngestValidatePlan:
    def test_ingest_stack_services(self, tmp_path: Path) -> None:
        """ingest lists every service in the web-stack bundle."""
        out = tmp_path / "ingest.json"
        proc = run_ingest(STACK, out)
        assert proc.returncode == 0, proc.stderr
        data = json.loads(out.read_text(encoding="utf-8"))
        bundle = data["bundles"][STACK_BUNDLE]
        names = {s["name"] for s in bundle["services"]}
        assert names == {"boot", "edge", "logger", "probe", "relay"}

    def test_ingest_matches_reference(self, tmp_path: Path) -> None:
        """CLI ingest matches independent protected reference parser."""
        out = tmp_path / "ingest.json"
        run_ingest(STACK, out)
        cli = json.loads(out.read_text(encoding="utf-8"))
        ref = build_ingest(STACK)
        assert cli["bundles"][STACK_BUNDLE] == ref["bundles"][STACK_BUNDLE]

    def test_soft_dep_form_stores_child_parent(self, tmp_path: Path) -> None:
        """soft dep CHILD soft PARENT stores [CHILD, PARENT], not [CHILD, soft]."""
        out = tmp_path / "ingest.json"
        proc = run_ingest(SOFT, out)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        soft_deps = cli["bundles"][SOFT_BUNDLE]["soft_deps"]
        assert soft_deps == [["probe", "tap"]]
        ref = build_ingest(SOFT)["bundles"][SOFT_BUNDLE]
        assert ref["soft_deps"] == [["probe", "tap"]]

    def test_plan_matches_reference(self, tmp_path: Path) -> None:
        """plan order matches independent topological reference."""
        out = tmp_path / "plan.json"
        proc = run_plan(STACK, STACK_BUNDLE, out)
        assert proc.returncode == 0, proc.stderr
        order = json.loads(out.read_text(encoding="utf-8"))["order"]
        bundle = build_ingest(STACK)["bundles"][STACK_BUNDLE]
        assert order == topo_plan(bundle)

    def test_plan_not_alphabetical_trap(self, tmp_path: Path) -> None:
        """Alphabetical order would start edge before logger; plan must not."""
        out = tmp_path / "plan.json"
        run_plan(STACK, STACK_BUNDLE, out)
        order = json.loads(out.read_text(encoding="utf-8"))["order"]
        assert order.index("logger") < order.index("edge")
        assert order.index("relay") < order.index("edge")

    def test_validate_cycle_exits_two(self, tmp_path: Path) -> None:
        """validate detects cycle fixture with exit 2."""
        proc = run_validate(CYCLE, CYCLE_BUNDLE)
        assert proc.returncode == 2
        assert proc.stderr.strip().startswith("cycle:")
        bundle = build_ingest(CYCLE)["bundles"][CYCLE_BUNDLE]
        ref = find_cycle(bundle)
        assert ref is not None
        assert "alpha" in proc.stderr and "beta" in proc.stderr

    def test_validate_stack_ok(self, tmp_path: Path) -> None:
        """Acyclic stack validate exits 0."""
        proc = run_validate(STACK, STACK_BUNDLE)
        assert proc.returncode == 0, proc.stderr

    def test_seed_injected_cycle_on_validate(self, tmp_path: Path) -> None:
        """Seed-derived cycle pair fails validate, not only export."""
        tag = hashlib.sha256(SEED.encode()).hexdigest()[:6]
        copy = tmp_path / "seed-cycle"
        copy.mkdir()
        (copy / "loop.bundle").write_text(
            f"bundle loop-{tag}\n"
            f"service x-{tag} longrun\nservice y-{tag} longrun\n"
            f"dep x-{tag} hard y-{tag}\ndep y-{tag} hard x-{tag}\n"
            f"longrun x-{tag}\nlongrun y-{tag}\n",
            encoding="utf-8",
        )
        proc = run_validate(copy, f"loop-{tag}")
        assert proc.returncode == 2
        assert f"x-{tag}" in proc.stderr

    def test_parser_touch_records_bundle_paths(self, tmp_path: Path) -> None:
        """Ingest records each parsed bundle path in parser touch file."""
        out = tmp_path / "ingest.json"
        touch = Path("/app/output/.parser-touch")
        run_ingest(STACK, out)
        touched = {line.strip() for line in touch.read_text(encoding="utf-8").splitlines() if line.strip()}
        assert any("web-stack.bundle" in p for p in touched)


class TestReadyAndApply:
    def test_ready_blocked_when_parents_down(self, tmp_path: Path) -> None:
        """Longruns stay not-ready while hard parents are down in rc state."""
        out = tmp_path / "ready.json"
        write_rc(STATE, {"boot": "up"})
        proc = run_ready(STACK, STACK_BUNDLE, STATE, out)
        assert proc.returncode == 0, proc.stderr
        data = load_json(out)
        bundle = build_ingest(STACK)["bundles"][STACK_BUNDLE]
        ref = ready_map(bundle, {"boot": "up"})
        assert data["longruns"]["logger"]["ready"] is True
        assert data["longruns"]["relay"]["ready"] is False
        assert "logger" in data["longruns"]["relay"]["blocked_by"]
        assert data["longruns"] == ref

    def test_ready_all_when_chain_up(self, tmp_path: Path) -> None:
        """All longruns ready once hard ancestor chain is up."""
        out = tmp_path / "ready.json"
        write_rc(
            STATE,
            {"boot": "up", "logger": "up", "relay": "up", "edge": "up"},
        )
        proc = run_ready(STACK, STACK_BUNDLE, STATE, out)
        assert proc.returncode == 0, proc.stderr
        data = load_json(out)
        for meta in data["longruns"].values():
            assert meta["ready"] is True
            assert meta["blocked_by"] == []

    def test_ready_not_eager_before_deps(self, tmp_path: Path) -> None:
        """Empty rc state must block every longrun (no eager ready)."""
        out = tmp_path / "ready.json"
        run_ready(STACK, STACK_BUNDLE, STATE, out)
        data = load_json(out)
        assert data["longruns"]["logger"]["ready"] is False
        assert "boot" in data["longruns"]["logger"]["blocked_by"]

    def test_apply_staging_post_rc(self, tmp_path: Path) -> None:
        """staging.json is written after s6-rc change with staged_at post-rc."""
        proc = run_apply(STACK, STACK_BUNDLE, "web-stack-v1", STATE)
        assert proc.returncode == 0, proc.stderr
        staging = load_json(Path("/app/state/staging.json"))
        assert staging["staged_at"] == "post-rc"
        assert staging["bundle_id"] == "web-stack-v1"
        rc = load_json(STATE / "services.json")
        assert rc.get("boot") == "up"

    def test_apply_brings_services_up_in_order(self, tmp_path: Path) -> None:
        """Mock rc records every service up after apply."""
        run_apply(STACK, STACK_BUNDLE, "web-stack-v2", STATE)
        rc = load_json(STATE / "services.json")
        for name in ("boot", "logger", "relay", "edge", "probe"):
            assert rc[name] == "up"

    def test_ready_after_partial_apply(self, tmp_path: Path) -> None:
        """Ready reflects partial rc state after apply transitions."""
        run_apply(STACK, STACK_BUNDLE, "web-stack-v3", STATE)
        out = tmp_path / "ready.json"
        run_ready(STACK, STACK_BUNDLE, STATE, out)
        data = load_json(out)
        assert all(meta["ready"] for meta in data["longruns"].values())


class TestExportAndIdempotentApply:
    def test_export_includes_soft_edges(self, tmp_path: Path) -> None:
        """export lists soft dependencies and accurate edge_count."""
        out = tmp_path / "graph.json"
        proc = run_export(SOFT, SOFT_BUNDLE, out)
        assert proc.returncode == 0, proc.stderr
        data = load_json(out)
        bundle = build_ingest(SOFT)["bundles"][SOFT_BUNDLE]
        ref_edges = all_edges(bundle)
        assert data["edge_count"] == len(ref_edges)
        assert data["edges"] == ref_edges
        soft = [e for e in data["edges"] if e["kind"] == "soft"]
        assert len(soft) == 1
        assert soft[0]["from"] == "probe"
        assert soft[0]["to"] == "tap"

    def test_export_stack_hard_only_count(self, tmp_path: Path) -> None:
        """web-stack export matches parser-derived hard edges only."""
        out = tmp_path / "graph.json"
        proc = run_export(STACK, STACK_BUNDLE, out)
        assert proc.returncode == 0, proc.stderr
        data = load_json(out)
        bundle = build_ingest(STACK)["bundles"][STACK_BUNDLE]
        ref_edges = all_edges(bundle)
        assert data["edge_count"] == len(ref_edges)
        assert data["edges"] == ref_edges
        assert all(e["kind"] == "hard" for e in data["edges"])

    def test_export_cycle_exits_two(self, tmp_path: Path) -> None:
        """export rejects cyclic bundle."""
        out = tmp_path / "graph.json"
        proc = run_export(CYCLE, CYCLE_BUNDLE, out)
        assert proc.returncode == 2
        assert "cycle:" in proc.stderr

    def test_validate_and_export_both_detect_cycle(self, tmp_path: Path) -> None:
        """validate and export both fail on cycle fixture."""
        v = run_validate(CYCLE, CYCLE_BUNDLE)
        out = tmp_path / "graph.json"
        e = run_export(CYCLE, CYCLE_BUNDLE, out)
        assert v.returncode == 2
        assert e.returncode == 2

    def test_apply_idempotent_bundle_id(self, tmp_path: Path) -> None:
        """Re-applying same bundle_id does not duplicate transitions or re-stage."""
        bid = "web-stack-v1"
        staging_path = Path("/app/state/staging.json")
        first = run_apply(STACK, STACK_BUNDLE, bid, STATE)
        assert first.returncode == 0, first.stderr
        log1 = json.loads(Path("/app/state/transition-log.json").read_text(encoding="utf-8"))
        applied1 = load_json(Path("/app/state/applied.json"))
        staging1 = load_json(staging_path)
        assert staging1["staged_at"] == "post-rc"
        second = run_apply(STACK, STACK_BUNDLE, bid, STATE)
        assert second.returncode == 0, second.stderr
        log2 = json.loads(Path("/app/state/transition-log.json").read_text(encoding="utf-8"))
        applied2 = load_json(Path("/app/state/applied.json"))
        staging2 = load_json(staging_path)
        assert log1 == log2
        assert staging1 == staging2
        assert applied1["apply_count"] == applied2["apply_count"] == 1

    def test_apply_new_bundle_id_increments(self, tmp_path: Path) -> None:
        """Different bundle_id performs a fresh apply."""
        run_apply(STACK, STACK_BUNDLE, "web-stack-a", STATE)
        run_apply(STACK, STACK_BUNDLE, "web-stack-b", STATE)
        applied = load_json(Path("/app/state/applied.json"))
        assert applied["bundle_id"] == "web-stack-b"

    def test_seed_soft_edge_in_export(self, tmp_path: Path) -> None:
        """Hidden soft edge from seed bundle appears in export graph."""
        tag = hashlib.sha256(f"{SEED}:soft".encode()).hexdigest()[:6]
        copy = tmp_path / "seed-soft"
        copy.mkdir()
        (copy / "extra.bundle").write_text(
            f"bundle soft-{tag}\n"
            f"service root oneshot\n"
            f"service leaf longrun\n"
            f"service watcher oneshot\n"
            f"dep leaf hard root\n"
            f"soft dep watcher soft leaf\n"
            f"longrun leaf\n",
            encoding="utf-8",
        )
        out = tmp_path / "graph.json"
        proc = run_export(copy, f"soft-{tag}", out)
        assert proc.returncode == 0, proc.stderr
        data = load_json(out)
        assert data["edge_count"] == 2
        soft = [e for e in data["edges"] if e["kind"] == "soft"]
        assert soft == [{"from": "watcher", "to": "leaf", "kind": "soft"}]
