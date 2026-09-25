#!/usr/bin/env python3
"""Collapse-risk check for netlink route nexthop multipath bind repair."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEST_FILE = ROOT / "tests" / "test_outputs.py"

HARD = {
    "test_tb3_hidden_cross_stage_chain",
    "test_tb3_hidden_single_path_metrics_passes_guard",
    "test_cross_run_nh_ids_reset_between_invocations",
    "test_partial_golden_route_table_digest_trap",
    "test_partial_golden_snapshot_routes_weight_sort_still_wrong_digest",
    "test_partial_golden_guard_inverted_rejects_valid_single_path",
    "test_partial_golden_bind_guard_nh_still_wrong_tb3_hidden",
    "test_partial_golden_decode_guard_rejects_multipath_metrics_leak",
    "test_partial_golden_decode_bind_nh_still_wrong_export_digest",
    "test_procedural_chain_bundle",
}


def main() -> int:
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"))
    tests: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            tests.append(node.name)
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                    tests.append(item.name)

    hard = [t for t in tests if t in HARD]
    if len(hard) < len(HARD):
        print("missing hard tests:", sorted(HARD - set(hard)))
        return 1

    print(f"total tests: {len(tests)}")
    print(f"hard workflow tests: {len(hard)}")
    print(
        "collapse risk: LOW — decode, bind, guard, export_nh snapshot_routes, "
        "and export digest must align across bundled and hidden fixtures"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
