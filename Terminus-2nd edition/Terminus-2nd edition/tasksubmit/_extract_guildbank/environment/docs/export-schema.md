# Guild audit export schema

Path: `/app/output/guild-audit.json`

```json
{
  "guild_id": "string",
  "gold_balance": 0,
  "vault_stack_qty": 0,
  "withdrawn_slice_qty": 0,
  "committed_audit_count": 0,
  "orphan_audit_count": 0,
  "interest_applied_total": 0
}
```

- `vault_stack_qty`: `SUM(item_stacks.quantity)` for the guild.
- `withdrawn_slice_qty`: `SUM(withdraw_slices.quantity)` for the guild.
- `committed_audit_count`: audit rows with `committed=1`.
- `orphan_audit_count`: committed audit rows lacking a durable matching mutation per `/app/docs/audit-order.md`.
- `interest_applied_total`: per `/app/docs/interest-journal.md`.
