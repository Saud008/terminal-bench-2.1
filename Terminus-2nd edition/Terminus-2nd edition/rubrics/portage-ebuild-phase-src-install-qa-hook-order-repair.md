# Platform rubric — portage-ebuild-phase-src-install-qa-hook-order-repair

**Task folder:** tasks/portage-ebuild-phase-src-install-qa-hook-order-repair/
**Written:** 2026-07-19T16:46:30Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent records src_install steps in /app/state/phase-trace.json with normalize_d before qa_preflight, +3
Agent applies fperms before dosbin so setuid bits from the manifest survive dosbin, +3
Agent keeps every symlink under D resolving inside the destination root, +3
Agent normalizes directories under D to mode 0755 before QA preflight reads the tree, +2
Agent writes a merged ledger record to /app/state/merge-ledger.json only after src_test succeeds, +3
Agent exits non-zero on src_test failure and appends no merge record for that package, +3
Agent propagates ebuild_die failures from subshell groups so full runs abort, +2
Agent leaves /app/docs and /app/fixtures unchanged, +1
Agent reorders QA ahead of normalize_d so preflight runs on an unnormalized tree, -3
Agent strips setuid during dosbin even after fperms applied the bit, -3
Agent appends a merged ledger record when src_test fails or die fires in a subshell, -5
