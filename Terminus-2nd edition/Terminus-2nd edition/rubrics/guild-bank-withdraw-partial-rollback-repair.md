# Platform rubric — guild-bank-withdraw-partial-rollback-repair

**Task folder:** tasks/guild-bank-withdraw-partial-rollback-repair/

Agent rebuilds guildbankd with verifier-rebuild.sh after Go edits, +2
Agent edits only /app/internal/store/store.go, /app/internal/bank/dao.go, /app/internal/bank/withdraw.go, /app/internal/bank/transfer.go, and /app/internal/interest/accrual.go, +3
Agent partial stack withdraw decrements vault rows and records withdraw_slices, +3
Agent concurrent gold withdraws never drive treasury balance negative, +3
Agent rejected gold withdraw leaves committed audit count at zero, +3
Agent bound vault stacks reject transfer-out with HTTP 409, +2
Agent interest replay credits each period exactly once, +3
Agent export totals match independent vault and slice quantity sums, +2
Agent fixes withdraw split alone while dao still commits audit on reject, -3
Agent fixes transfer bound check alone while interest replay still double-credits, -3
Agent fixes accrual idempotency alone while partial withdraw still skips slice rows, -3
Agent modifies protected docs, config, fixtures, or HTTP wiring sources, -5
