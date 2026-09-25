#!/usr/bin/env python3
"""Add docstrings and path literals for audit."""
from __future__ import annotations

import ast
import re
from pathlib import Path

p = Path("tasks/isc-dhcp-failover-bndupd-lease-atlas/tests/test_outputs.py")
text = p.read_text(encoding="utf-8")
text = text.replace(
    'SNAPSHOT = APP / "state/dhcp-staging.json"',
    'SNAPSHOT = APP / "state/dhcp-staging.json"  # /app/state/dhcp-staging.json',
)
text = text.replace(
    'OUTPUT = APP / "output/lease-atlas.json"',
    'OUTPUT = APP / "output/lease-atlas.json"  # /app/output/lease-atlas.json',
)

docs = {
    "test_fixture_catalog_present": "Verifies public DHCP fixtures exist under /app/fixtures.",
    "test_fixture_sha256_integrity": "Guards fixture bytes so agents cannot edit inputs to pass.",
    "test_cli_flags_required": "Checks bndupd replay requires config log and snapshot flags.",
    "test_basic_active_ack_atlas": "Asserts /app/output/lease-atlas.json matches reference after basic ack.",
    "test_staging_matches_model": "Checks /app/state/dhcp-staging.json matches independent reference snapshot.",
    "test_publish_reads_staging_only": "Ensures publish reads /app/state/dhcp-staging.json without fixture logs.",
    "test_chaddr_case_normalize": "Validates chaddr normalization and equal-tstp status supersede.",
    "test_mclt_partner_down": "Verifies MCLT holdover blocks free while partner is down.",
    "test_splitbrain_quarantine": "Checks active IP conflicts become quarantine rows with checksum.",
    "test_supersede_tstp": "Asserts higher tstp supersedes prior binding status.",
    "test_pending_without_ack": "Ensures unacked BNDUPD stays pending and out of committed bindings.",
    "test_multi_pool_peers": "Validates multi-peer supersede and stale ignore against reference.",
    "test_bindings_sorted_by_key": "Asserts atlas bindings sort by binding_key ascending.",
    "test_tb3_mclt_boundary": "Runs hidden /opt/verifier-fixtures MCLT boundary trap against reference.",
    "test_tb3_ack_skew_split": "Runs hidden ack-skew split-brain trap against reference.",
    "test_all_public_logs_match_model": "Parametric parity across all public logs for atlas export.",
    "test_cross_run_persistence": "Validates second replay merges prior /app/state/dhcp-staging.json.",
    "test_purge_clears_prior": "Checks --purge starts fresh and drops prior staging bindings.",
    "test_omapi_decoy_overlay_fails_alone": "Confirms omapi_decoy wrap alone cannot satisfy reference atlas.",
    "test_single_module_patch_is_insufficient": "Proves each single golden module patch still mismatches reference.",
    "test_ingest_only_poison_still_fails_export_contract": "Ingest modules fixed with broken export still fail atlas contract.",
    "test_export_only_poison_fails_without_ingest": "Export-only golden leaves pending-ack semantics wrong.",
    "test_probe_staging_artifact_required": "Probe that staging schema docs name dhcp-staging.json.",
    "test_probe_decoy_module_present": "Probe that omapi_decoy wrap module exists off the hot path.",
}

for fn, doc in docs.items():
    pat = rf"(def {fn}\(.*\)\s*->\s*None:\n)( +)(?![\"'])"
    m = re.search(pat, text)
    if not m:
        pat = rf"(def {fn}\(.*\):\n)( +)(?![\"'])"
        m = re.search(pat, text)
    if not m:
        print("skip", fn)
        continue
    indent = m.group(2)
    # already has docstring?
    after = text[m.end() : m.end() + 10]
    if after.lstrip().startswith('"""') or after.lstrip().startswith("'''"):
        continue
    insert = f'{m.group(1)}{indent}"""{doc}"""\n{indent}'
    text = text[: m.start()] + insert + text[m.end() :]

p.write_text(text, encoding="utf-8")
tree = ast.parse(text)
missing = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
        if not ast.get_docstring(node):
            missing.append(node.name)
    if isinstance(node, ast.ClassDef):
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                if not ast.get_docstring(item):
                    missing.append(item.name)
print("still missing", missing)
