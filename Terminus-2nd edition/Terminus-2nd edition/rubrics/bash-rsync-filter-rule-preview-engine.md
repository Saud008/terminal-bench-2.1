# Platform rubric — bash-rsync-filter-rule-preview-engine

**Task folder:** tasks/bash-rsync-filter-rule-preview-engine/

Agent implements rsyncprev ingest loading tree manifest sender receiver paths and filter rules, +3
Agent merges root rules then per-directory .rsync-filter rows in ancestor order for each path, +3
Agent applies first matching filter rule for transfer include or exclude verdict, +3
Agent matches root-anchored patterns and directory /** globs including the directory path itself, +3
Agent sets merge_depth to merge_cascade ledger length including root layer, +2
Agent classifies delete_risk protected when any P rule matches a receiver path, +3
Agent classifies delete_risk candidate for receiver-only paths matching R or exclude transfer, +3
Agent sets prune true for excluded directory paths without file extension, +2
Agent exports path_verdicts sorted by path with summary counts in rsync_filter_preview_atlas.json, +3
Agent honors TB3_TREE_ROOT for hidden tree manifests under verifier fixtures, +2
Agent fixes only parse_filters token mapping while merge order stays reversed, -3
Agent patches decoy digest_story_helper onto ingest or export hot path, -3
Agent uses last matching rule instead of first match for transfer verdict, -5
Agent omits receiver-only paths from compile union evaluation, -3
Agent sorts export rows by transfer before path breaking deterministic order, -3
