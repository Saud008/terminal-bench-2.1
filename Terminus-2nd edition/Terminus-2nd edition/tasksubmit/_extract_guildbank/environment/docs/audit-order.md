# Audit entry ordering

`audit_entries` records successful treasury mutations.

Rules:

- Insert audit rows **only after** the mutating SQLite transaction commits successfully.
- `committed` must be `1` only for rows whose matching mutation is durable in `guilds`, `item_stacks`, `withdraw_slices`, or `player_stacks`.
- Failed or rolled-back withdraws must **not** create committed audit rows.
- Rejected insufficient-gold withdraws must not increase `committed_audit_count`.

`orphan_audit_count` in export counts committed audit rows whose payload does not match durable treasury state: gold withdraw audits whose recorded balance disagrees with `guilds.gold_balance`, reject audits missing a post-balance field, or stack withdraw audits recording more quantity than `withdraw_slices` holds.
