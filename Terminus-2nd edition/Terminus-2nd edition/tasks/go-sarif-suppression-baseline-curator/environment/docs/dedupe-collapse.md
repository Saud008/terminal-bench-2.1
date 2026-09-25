# Dedupe collapse

After rule canonicalization and path remap, collapse duplicate findings that share the same rule_key, remapped uri, and start_line.

## Severity order

Keep the finding with the highest severity. Rank highest to lowest: error, warning, note, any other level.

Tie break: lowest finding_id lexicographic.

Collapsed findings proceed to suppression and baseline reconciliation.
