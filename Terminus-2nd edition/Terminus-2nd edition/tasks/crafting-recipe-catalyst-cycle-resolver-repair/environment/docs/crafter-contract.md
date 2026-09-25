# Crafter contract

## Commands

All paths are absolute. JSON is written to stdout; non-zero exit codes mark rejection.

| Command | Exit 0 | Exit non-zero |
|---------|--------|---------------|
| `crafter seed` | profile loaded | I/O or schema error |
| `crafter preview` | craft viable | exit **2** when preview rejects |
| `crafter apply` | craft committed | exit **1** on any rejection |
| `crafter validate-graph` | acyclic graph | exit **3** when cycles exist |
| `crafter export` | JSON written | I/O error |

## Preview vs commit

- **Preview** is read-only for inventory persistence except it must **never** deduct inputs, outputs, or catalyst charges.
- **Apply** mutates SQLite inventory atomically: either the full craft succeeds or inventory is unchanged from before the apply call.

## Catalyst

When a recipe lists a catalyst with `consumed: false`, the catalyst quantity must remain in inventory after both preview and apply. The presence check uses `catalyst.qty` as-is (not multiplied by batch size). When `consumed: true`, require and deduct `catalyst.qty * batch_qty` only on successful **apply**, never on preview.

## Failed craft rollback

If output placement fails (inventory full, stack overflow, missing materials), **apply** must leave inventory identical to the pre-apply snapshot. Partial input deduction is forbidden.

## Substitutes

Resolve the substitute map **before** multiplying ingredient quantities by batch size. Inventory checks and deductions use substituted item ids.

## Stackable outputs

Before merging into an existing stack, verify `existing_qty + output_qty <= stack_max` for that item. Reject the craft when the merge would overflow. Count new slots only after overflow checks pass.

## Graph validation

Build directed edges from consumer recipe to producer recipe for:

1. Every input item that another recipe outputs.
2. Every catalyst item that another recipe outputs.

Report all discovered cycles. Bundled `/app/fixtures/recipes/cycle-trap.json` must be cyclic; `/app/fixtures/recipes/base.json` must be acyclic.
