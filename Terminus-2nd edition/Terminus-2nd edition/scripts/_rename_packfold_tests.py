from pathlib import Path

p = Path("tasks/git-packfile-delta-chain-base-offset-closure-atlas/tests/test_outputs.py")
t = p.read_text(encoding="utf-8")
repl = {
    "TestPfoldClosureAtlasCli": "TestGitPackDeltaResolve",
    "TestPfoldTb3PackVault": "TestGitPackVerifierPackVault",
    "test_pfold_bundled_fixture_digest_lock": "test_gitpack_oid_fixture_sha_guard",
    "test_pfold_state_and_output_dirs_present": "test_gitpack_vfs_state_output_dirs",
    "test_pfold_end_to_end_resolve_seal_outputs": "test_gitpack_resolve_seal_artifact_paths",
    "test_pfold_cli_missing_flags_status_two": "test_gitpack_argv_required_exit_two",
    "test_pfold_resolve_quarantine_corrupt_jsonl": "test_gitpack_corrupt_jsonl_exit_one",
    "test_pfold_basic_batch_watermark_coalesce": "test_gitpack_basic_ofs_delta_closure",
    "test_pfold_chain_depth_breaks_offset_rank": "test_gitpack_ref_delta_depth_beats_offset",
    "test_pfold_type_tag_size_class_object_keys": "test_gitpack_oid_type_tag_size_class_split",
    "test_pfold_empty_shard_keeps_watermark_gen": "test_gitpack_void_shard_chain_gen_persist",
    "test_pfold_seal_reads_staging_atlas_only": "test_gitpack_seal_reads_closure_atlas_only",
    "test_pfold_manifest_hash_embeds_type_tag": "test_gitpack_entry_sha256_type_tag_bits",
    "test_pfold_persist_resume_cross_run_resolve": "test_gitpack_resume_second_pass_chain",
    "test_pfold_verifier_seed_fixture_rotation": "test_gitpack_verifier_seed_oid_batch",
    "test_pfold_seed_matrix_watermark_replay": "test_gitpack_param_oid_batch_matrix",
    "test_pfold_reference_rank_chain_gen_depth": "test_gitpack_ref_row_beats_depth_gen",
    "test_pfold_single_module_overlay_incomplete": "test_gitpack_one_crate_golden_trap",
    "test_pfold_legacy_deflate_window_decoy_insufficient": "test_gitpack_deflate_legacy_decoy_fails",
    "test_pfold_tb3_chain_depth_canonical_winner": "test_gitpack_tb3_depth99_oid_winner",
    "test_pfold_tb3_commit_blob_type_divergence": "test_gitpack_tb3_commit_blob_divergence",
    "test_pfold_tb3_two_batch_resume_watermark": "test_gitpack_tb3_two_pass_chain_gen",
    "test_pfold_tb3_sealed_manifest_root_hash": "test_gitpack_tb3_pack_root_sha256",
    "_overlay_one_golden_module": "_apply_single_crate_patch",
}
for a, b in repl.items():
    t = t.replace(a, b)
t = t.replace('EXTRA_SEEDS = ["north", "south", "east"]', 'EXTRA_SEEDS = ["delta", "gamma", "theta"]')
p.write_text(t, encoding="utf-8")
print("done")
