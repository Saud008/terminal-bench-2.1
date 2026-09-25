# Platform rubric — rust-xanes-fluorescence-window-closure

**Task folder:** tasks/rust-xanes-fluorescence-window-closure/
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent matches independent verifier digests on catalog close exports, +3
Agent applies seeded monochromator jitter when --seed is set, +3
Agent orders fluorescence channels by spectroscopic rank from the edge-ordinal contract, +3
Agent refuses undeclared ?edge_code windows with status error and exit code 1, +3
Agent emits closure_digest and all_channels_sorted per closure-schema.md, +3
Agent fits the pre-edge baseline before window integration, +2
Agent pops every scope-stack frame including empty-channel windows, +2
Agent matches hidden /opt/verifier-fixtures/xanes-delta trap digests, +2
Agent rebuilds xanesctl via cargo in the verifier path, +2
Agent leaves /app/docs and /app/fixtures unchanged, +1
Agent resets /app/output before cross-run close exports, +1
Agent leaves seeded deep-nest close digests mismatched after edits, -3
Agent allows undeclared ?edge markers to export status ok, -3
Agent leaves multi-edge channel order mismatched to spectroscopic rank, -3
Agent omits all_channels_sorted or closure_digest from the export, -2
Agent skips scope pop when a window declares zero channels, -2
Agent routes close through the decoy_plot module, -2
Agent edits bundled fixtures or docs instead of core modules, -2
