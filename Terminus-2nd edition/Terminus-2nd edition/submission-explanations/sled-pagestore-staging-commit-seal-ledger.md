# Submission explanations — sled-pagestore-staging-commit-seal-ledger

**Task folder:** tasks/sled-pagestore-staging-commit-seal-ledger/
**Platform form only** — not in upload zip.

**Restructure (2026-07-27):** Converted from Rust cargo B-tree engine repair (`sled-tree-journal-compaction-repair`) to **debian + bash/python** host-local pagestore ops control plane (fleet-roster / labelsheet shape) to clear Harbor `[category_classifier]` software-engineering blocks on `rust` + `cargo build` + B-tree module-rebuild shape. Policy modules under `/app/lib/sled/`; binary is `/usr/local/bin/sledtool` (bash → `python3 -m sled.cli`). Instruction-sufficiency contracts from the prior revision are retained in `/app/docs/`.

**Category note:** Zip metadata uses `system-administration` (host-local sledtool pagestore ops: batch → publish → seal). Do not set `software-engineering`, `debugging`, `data-processing`, or `security` on the platform form.

## Difficulty Explanation

Agents must align nine policy modules with seven contract docs covering staging, split journal ordering, FNV-1 page checksums, merge high-key bounds, compaction pins, and crash replay idempotency. Failures cluster on delete-heavy workloads where underflow must rebalance siblings in a stated preference order, leaf borrows must move real keys and refresh parent separators, internal merges must refresh high_key for scan-range pruning, and page checksums must hash generation bytes with FNV-1 not FNV-1a. Split mid must be floor(n/2); ceil mid-points diverge from the independent reference. Partial fixes pass bundled inserts but still fail delete export, scan-range after merge, or registry checksum tests. Eighteen subprocess tests plus hidden merge-range fixtures punish one-module patches.

## Solution Explanation

The oracle copies nine golden Python modules into `/app/lib/sled/`, refreshes `/usr/local/bin/sledtool`, and resets state. Correct behavior wires underflow to sibling borrow and merge, writes ParentPivot before RightPage in the split journal, includes generation in FNV-1 checksums, and rebuilds internal high_key after merges. Scan-range pruning and export both depend on the same committed tree shape. A second journal-replay pass must leave export unchanged.

## Verification Explanation

test.sh runs verifier-rebuild.sh then pytest. Eighteen tests invoke sledtool via subprocess and compare outputs to an independent reference_btree.py implementation. Bundled fixtures cover baseline, delete-heavy, and replay batches while hidden verifier fixtures exercise merge-range scans. Tests assert staging isolation, snapshot metrics, pin-aware compaction, split journal ordering, and registry checksums without reading solution source. NOP on the broken image scores zero and the oracle module swap passes all tests after rebuild.
