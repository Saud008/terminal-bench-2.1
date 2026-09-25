# Planner CLI catalog

Binary: /app/bin/geoboxplay

Subcommands:
- load-level (alias bootstrap-level) — --level <name> --run-id <id>
- score-round (alias tally-round) — --run-id <id>
- seal-atlas (alias publish-atlas) — --run-id <id> --output <path>

Load-level implementation entry: /app/internal/mbx7/w0/wrap_stage.sh
Seal-atlas implementation entry: /app/internal/mbx7/w7/emit_stage.sh
Score-round and rulecard shells live under /app/internal/mbx7/ as well.

Environment overrides:
- TB3_LEVEL_DIR — level pack root (default /app/fixtures/levels/)
- TB3_PLAY_SALT — appended to each filter pin name at load-level time
- TB3_PLAY_DIGITS — fixed precision for affinity lines in the atlas digest (default 4)
