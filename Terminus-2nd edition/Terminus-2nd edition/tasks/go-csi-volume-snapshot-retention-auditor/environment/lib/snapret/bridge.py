from __future__ import annotations

from typing import Any

from snapret import analyze_pass, cluster_load, fleet_store, vol_report


def materialize_fleet_graph(scenario: str, fixture_root: str) -> dict[str, Any]:
    cluster = cluster_load.load_cluster(scenario, fixture_root)
    return {"engine": "snapretctl", "scenario": scenario, "cluster": cluster}


def persist_fleet_graph(snap: dict[str, Any]) -> None:
    fleet_store.write_fleet_graph("", snap)


def run_analyze_pass(scenario: str) -> None:
    analyze_pass.run(scenario)


def seal_retention_report(
    scenario: str, report_path: str = "", dangling_path: str = ""
) -> None:
    vol_report.emit(scenario, report_path, dangling_path)
