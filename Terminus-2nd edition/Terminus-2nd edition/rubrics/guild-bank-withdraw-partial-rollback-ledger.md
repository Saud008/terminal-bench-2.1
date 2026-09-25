# Platform rubric — guild-bank-withdraw-partial-rollback-ledger

**Task folder:** tasks/guild-bank-withdraw-partial-rollback-ledger/

Agent rebuilds guildbankd with verifier-rebuild.sh after Go edits, +2
Agent partial stack withdraw decrements vault rows and records withdraw_slices, +3
Agent full stack withdraw removes the vault row and records the full quantity, +2
Agent concurrent gold withdraws never drive treasury balance negative, +3
Agent rejected gold withdraw leaves committed audit count at zero, +3
Agent successful gold withdraw persists a committed non-orphan audit row, +2
Agent export orphan_audit_count rises when a committed gold audit disagrees with durable balance, +2
Agent bound vault stacks reject transfer-out with HTTP 409, +2
Agent interest replay credits each period exactly once, +3
Agent repeated interest run for the same period does not double-credit gold, +3
Agent export totals match independent vault and slice quantity sums, +2
Agent fixes withdraw split alone while dao still commits audit on reject, -3
Agent fixes transfer bound check alone while interest replay still double-credits, -3
Agent fixes accrual idempotency alone while partial withdraw still skips slice rows, -3
Agent modifies protected docs config or fixtures, -5
