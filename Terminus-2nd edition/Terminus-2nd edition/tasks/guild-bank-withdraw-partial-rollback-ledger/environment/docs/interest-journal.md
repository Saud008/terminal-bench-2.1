# Interest journal and crash replay

Table `interest_journal` keys `(period_id, guild_id)`.

Statuses:

- `started` — journal row created, accrual in flight
- `applied` — interest credited for that period

`POST /v1/admin/interest/run` accrues one interest period for the guild. Interest follows the configured rate on the current gold balance, with a minimum credit of 1 when balance is greater than zero. Each `(period_id, guild_id)` is credited at most once. When the period is already `applied`, a repeated run returns the journaled `interest_amount` without mutating `gold_balance` again.

`POST /v1/admin/interest/replay` completes a period stuck in `started` without double-crediting. When status is already `applied`, the response returns the existing result and `gold_balance` is unchanged.

`interest_applied_total` in export is `SUM(interest_amount)` for rows with `status='applied'`.
