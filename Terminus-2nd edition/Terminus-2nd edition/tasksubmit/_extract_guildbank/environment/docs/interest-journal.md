# Interest journal and crash replay

Table interest_journal keys (period_id, guild_id).

Statuses:

- started — journal row created, accrual in flight
- applied — interest credited exactly once

POST /v1/admin/interest/run accrues one interest period for the guild. Interest follows the configured rate on the current gold balance, with a minimum credit of 1 when balance is greater than zero. Journal rows record run state; applied rows credit guild gold once per period.

POST /v1/admin/interest/replay completes journal rows stuck in started after a crash, exactly once per period. If journal status is already applied, return the existing result without mutating gold_balance. Repeated replay for the same applied period must be idempotent.

interest_applied_total in export is SUM(interest_amount) for rows with status='applied'.
