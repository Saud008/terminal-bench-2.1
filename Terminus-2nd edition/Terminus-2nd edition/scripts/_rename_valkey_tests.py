from pathlib import Path

p = Path("tasks/valkey-stream-pending-claim-ledger-replay/tests/test_outputs.py")
t = p.read_text(encoding="utf-8")
repl = {
    "TestStreamReplayOutputs": "TestValkeyPelLedgerCli",
    "test_public_fixtures_present": "test_valkey_pel_public_fixture_guard",
    "test_protected_fixtures_integrity": "test_valkey_pel_fixture_sha_lock",
    "test_missing_required_flags_nonzero": "test_valkey_pel_argv_required_exit",
    "test_basic_readgroup_matches_reference_export": "test_valkey_pel_basic_readgroup_export",
    "test_snapshot_matches_reference": "test_valkey_pel_staging_snapshot_ref",
    "test_publish_reads_snapshot_only": "test_valkey_pel_publish_snapshot_only",
    "test_pending_claim_increments_delivery_count": "test_valkey_pel_claim_delivery_count",
    "test_trim_pel_skips_pending": "test_valkey_pel_trim_pel_skip",
    "test_ack_trim_removes_acked_from_stream_view": "test_valkey_pel_ack_trim_ids",
    "test_seed_order_beta_matches_reference": "test_valkey_pel_seed_order_beta",
    "test_export_pending_sorted_by_entry_id": "test_valkey_pel_pending_sorted",
    "test_hidden_pending_claim_starve_fixture": "test_valkey_pel_tb3_starve",
    "test_hidden_starve_claim_and_trim_interaction": "test_valkey_pel_tb3_trim_interaction",
    "test_all_public_ops_match_reference": "test_valkey_pel_all_public_ops_ref",
    "test_verifier_broken_library_available": "test_valkey_pel_broken_lib_mount",
    "test_verifier_golden_lib_mounted": "test_valkey_pel_golden_lib_mount",
    "test_decoy_wrap_only_patch_still_fails": "test_valkey_pel_decoy_wrap_fails",
    "test_single_module_patch_is_insufficient": "test_valkey_pel_one_module_trap",
    "test_read_only_patch_still_fails_pending_claim": "test_valkey_pel_read_only_trap",
    "test_verifier_seed_mutation": "test_valkey_pel_seed_mutation",
    "_single_module_patch": "_overlay_valkey_pel_module",
}
for a, b in repl.items():
    t = t.replace(a, b)
t = t.replace(
    '"""Behavioral verifier for streamreplay replay/publish semantics."""',
    '"""Valkey PEL verifier — ingest ops log, staging snapshot, export ledger via subprocess CLI."""',
)
p.write_text(t, encoding="utf-8")
print("done")
