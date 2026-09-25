# Audit entry semantics

`audit_entries` records successful treasury mutations for export. A row with `committed=1` should correspond to a durable mutation in `guilds`, `item_stacks`, `withdraw_slices`, or `player_stacks`. Rejected or rolled-back withdraws should not leave committed audit rows.

`orphan_audit_count` in export counts committed audit rows whose payload does not match durable treasury state: gold withdraw audits whose recorded balance disagrees with `guilds.gold_balance`, gold withdraw audits missing a post-balance field, or stack withdraw audits recording more quantity than `withdraw_slices` holds.
