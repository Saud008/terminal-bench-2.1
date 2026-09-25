# Platform rubric — godot-tscn-uid-remap-merge-repair

**Task folder:** tasks/godot-tscn-uid-remap-merge-repair/
**Written:** 2026-06-26T07:40:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent loads three-way ancestor bytes from the --base branch directory, +3
Agent applies seed overlay remap targets using remap_prefix and remap_suffix_mod, +3
Agent rewrites uid tokens on ext_resource and gd_scene lines during remap, +3
Agent takes --base branch content on true three-way conflicts not mtime, +3
Agent detects directed UID graph cycles and exits with code 2, +3
Agent reports orphan uid references after delete_on_merge omissions, +2
Agent normalizes merged file text to LF before ledger content_sha256, +2
Agent honors caller-resolved --base without re-applying base_flip_seed_mod, +2
Agent hardcodes the literal base/ directory as merge ancestor regardless of --base, -3
Agent picks newer filesystem mtime on three-way conflicts, -3
Agent rewrites res:// path strings without matching uid tokens, -2
Agent skips seed overlay remap_slot entry from seeds.json, -2
Agent omits export JSON when uid_graph_ok is false on cycle traps, -2
