# Conflict ledger emit

emit-conflicts writes JSON with:
- seed, scenario, possession_id
- conflict_groups: array sorted by group_key ascending
- summary: total_conflicts, signal_blocked, override_suppressed, possession_pairs
- audit_digest

Each conflict_groups row contains group_key, participants, window_start, window_end, blocks, reasons.

group_key is participants sorted ascending lexicographically then joined with pipe.

participants must be sorted ascending lexicographically.

blocks lists unique block_id values sorted by ascending kilometer from the scenario block table, then block_id lexicographically when kilometers tie per train-movement-authority-lattice.md.

reasons is a sorted list of reason tokens.

possession_pairs counts unordered possession-versus-possession overlaps only.

audit_digest is lowercase hex SHA-256 over compact JSON with no spaces. Object keys must be sorted alphabetically: override_suppressed, part_sort, possession_pairs, signal_blocked, total_conflicts. part_sort is the array of group_key strings sorted ascending lexicographically.
