"""Bundled debpol contract tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from aptpol_contract_math import (
    contract_report,
    contract_report as reference_report,
    effective_pin,
    graph_digest,
    rank_origins,
    read_stanzas,
    version_newer,
)
from aptpol_runner import CLI, GRAPH, build_and_report, invoke, wipe


def test_t30c695_q01():
    """Contract rows match independent math for vendor-fetch-dual."""
    wipe()
    out = build_and_report("vendor-fetch-dual", "run-alpha")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_report(Path("/app/fixtures/scenarios/vendor-fetch-dual"), "run-alpha")
    assert rep["install_candidates"] == ref["install_candidates"]


def test_t30c695_q02():
    """Staging JSON includes run id and fingerprint fields."""
    wipe()
    build_and_report("vendor-fetch-dual", "run-bravo")
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    assert graph["run_id"] == "run-bravo"
    assert "graph_digest" in graph
    assert "origin_fingerprint" in graph
    assert isinstance(graph["package_rows"], list)


def test_t30c695_q03():
    """Libssl3 row selects 3.0 line with priority 1001."""
    wipe()
    out = build_and_report("libssl-pin", "run-charlie")
    rep = json.loads(out.read_text(encoding="utf-8"))
    row = next(r for r in rep["install_candidates"] if r["package"] == "libssl3")
    assert row["chosen_version"].startswith("3.0.")
    assert row["effective_priority"] == 1001


def test_t30c695_q04():
    """Arm64 nginx selects debian-main row."""
    wipe()
    out = build_and_report("multiarch-nginx", "run-delta")
    rep = json.loads(out.read_text(encoding="utf-8"))
    row = next(r for r in rep["install_candidates"] if r["package"] == "nginx")
    assert row["chosen_version"] is not None
    assert row["origin_id"] == "debian-main"


def test_t30c695_q05():
    """Foobar row selects higher numeric colon prefix."""
    wipe()
    out = build_and_report("dpkg-epoch-tiebreak", "run-echo")
    rep = json.loads(out.read_text(encoding="utf-8"))
    row = next(r for r in rep["install_candidates"] if r["package"] == "foobar")
    assert row["chosen_version"].startswith("2:")


def test_t30c695_q06():
    """Audit digest stable across rebuild with same run id."""
    wipe()
    out1 = build_and_report("vendor-fetch-dual", "run-alpha")
    wipe()
    out2 = build_and_report("vendor-fetch-dual", "run-alpha")
    assert json.loads(out1.read_text())["audit_digest"] == json.loads(out2.read_text())["audit_digest"]


def test_t30c695_q07():
    """Snapshot hash matches contract helper output."""
    wipe()
    build_and_report("libssl-pin", "run-charlie")
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    expected = graph_digest(graph["run_id"], graph["origin_fingerprint"], graph["package_rows"])
    assert graph["graph_digest"] == expected


def test_t30c695_q08():
    """Continuation lines preserve multi uri field."""
    stanzas = read_stanzas(Path("/app/fixtures/scenarios/vendor-fetch-dual/sources.sources"))
    assert "vendor.example" in stanzas[0]["URIs"]


def test_t30c695_q09():
    """Default-Pin ordering is descending by numeric value."""
    stanzas = rank_origins(read_stanzas(Path("/app/fixtures/scenarios/vendor-fetch-dual/sources.sources")))
    assert int(stanzas[0].get("Default-Pin", "0")) >= int(stanzas[-1].get("Default-Pin", "0"))


def test_t30c695_q10():
    """Release revision sorts after tilde upstream segment."""
    assert version_newer("2.1-3", "2.1~rc1-1")


def test_t30c695_q11():
    """Version pin glob matches libssl3 3.0 line."""
    prefs = [{"Package": "libssl3", "Pin": "version 3.0.*", "Pin-Priority": "1001"}]
    assert effective_pin(prefs, "libssl3", "3.0.11-1~deb12u2") == 1001


def test_t30c695_q12():
    """Report subcommand reads staging JSON only."""
    wipe()
    build_and_report("vendor-fetch-dual", "run-alpha")
    Path("/app/work/run-alpha-policy-build.json").write_text("{}", encoding="utf-8")
    out = Path("/app/output/run-alpha-reexport.json")
    proc = invoke([str(CLI), "candidate-report", "--run-id", "run-alpha", "--output", str(out)])
    assert proc.returncode == 0
    assert json.loads(out.read_text(encoding="utf-8"))["install_candidates"]


def test_t30c695_q13():
    """Install rows sorted by package name ascending."""
    wipe()
    out = build_and_report("vendor-fetch-dual", "run-bravo")
    names = [r["package"] for r in json.loads(out.read_text())["install_candidates"]]
    assert names == sorted(names)


def test_t30c695_q14():
    """Repeated build-policy leaves staging file present."""
    wipe()
    for _ in range(2):
        proc = subprocess.run(
            [str(CLI), "build-policy", "--scenario", "vendor-fetch-dual", "--run-id", "run-bravo"],
            cwd="/app",
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr
    assert GRAPH.exists()


def test_t30c695_q15():
    """Redis-server row matches contract when pins tie."""
    wipe()
    out = build_and_report("redis-suite-bias", "run-foxtrot")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = contract_report(Path("/app/fixtures/scenarios/redis-suite-bias"), "run-foxtrot")
    row = next(r for r in rep["install_candidates"] if r["package"] == "redis-server")
    assert row == next(r for r in ref["install_candidates"] if r["package"] == "redis-server")


def test_t30c695_q16():
    """Curl row selects 7.x line with high priority."""
    wipe()
    out = build_and_report("vendor-fetch-dual", "run-alpha")
    row = next(r for r in json.loads(out.read_text())["install_candidates"] if r["package"] == "curl")
    assert row["chosen_version"].startswith("7.")
    assert row["effective_priority"] >= 990


def test_t30c695_q17():
    """Curl package rows include both origin ids."""
    wipe()
    build_and_report("vendor-fetch-dual", "run-alpha")
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    origins = {r["origin_id"] for r in graph["package_rows"] if r["package"] == "curl"}
    assert origins == {"debian-main", "vendor-backports"}


def test_t30c695_q18():
    """Redis suite scenario lists both source ids."""
    wipe()
    build_and_report("redis-suite-bias", "run-stg-1")
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    ids = {o.get("X-Source-Id") for o in graph["origins"]}
    assert ids == {"debian-main", "debian-backports"}


def test_t30c695_q19():
    """Query package roundtrips through staging JSON."""
    wipe()
    build_and_report("dpkg-epoch-tiebreak", "run-stg-2")
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    assert graph["queries"][0]["package"] == "foobar"


def test_t30c695_q20():
    """Libssl scenario loads at least two pin stanzas."""
    wipe()
    build_and_report("libssl-pin", "run-stg-3")
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    assert len(graph["preferences"]) >= 2


def test_t30c695_q21():
    """Staging snapshot includes hash and fingerprint fields."""
    wipe()
    build_and_report("vendor-fetch-dual", "run-bravo")
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    assert graph.get("graph_digest")
    assert graph.get("origin_fingerprint")


def test_t30c695_q22():
    """Build-policy collects multiple package rows before export."""
    wipe()
    proc = invoke([str(CLI), "build-policy", "--scenario", "libssl-pin", "--run-id", "run-ingest"])
    assert proc.returncode == 0
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    assert len(graph["package_rows"]) >= 2


def test_t30c695_q23():
    """Export subcommand emits rows without rebuild."""
    wipe()
    invoke([str(CLI), "build-policy", "--scenario", "dpkg-epoch-tiebreak", "--run-id", "run-export"])
    out = Path("/app/output/run-export-report.json")
    proc = invoke([str(CLI), "candidate-report", "--run-id", "run-export", "--output", str(out)])
    assert proc.returncode == 0
    assert json.loads(out.read_text(encoding="utf-8"))["install_candidates"]
