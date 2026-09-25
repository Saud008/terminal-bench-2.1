# Cutover rollout operations

This is the system-administration ops rationale for composing the hold-preview
gates into a single sealed rollout atlas ahead of a host-local graph-fleet
cutover. There is no remote cutover control plane.

Before fleet cutover administrators run a mutation-wave cutover job, they need a dry-run answer:
for each proposed commit, would the fleet **hold** it (and why) or **admit**
it? Getting that answer wrong in either direction is expensive — a silently
admitted policy-pinned attr leaks, and a wrongly held commit stalls the
cutover.

The gates compose in a fixed order per record:

1. **Preflight** decides whether the record is even considered, using only the
   live fleet state so the preview is stable regardless of edit order.
2. **Identity bind** pins blank-node commits onto the right existing node so
   the atlas does not sprout duplicate nodes across cutover cycles.
3. **Deny-pin hold** keeps policy-pinned attrs out of the previewed writes.
4. **Conflict precedence** makes same-target contention deterministic, so two
   operators previewing the same wave never see different winners.
5. **List coalesce** keeps localized (per-lang) list entries distinct while
   folding exact repeats.
6. **Schema-bump abort** guarantees a non-committing record is a true no-op —
   no leaked writes, no leaked schema marks.

The published atlas carries a deterministic `atlas_digest` so a downstream
cutover job can diff the current preview against the prior one and refuse to
proceed on an unexpected change. Wall-clock order is deliberately excluded
from every decision so the same wave always previews identically.
