# Platform rubric — bash-containerd-namespace-image-gc-planner

**Task folder:** tasks/bash-containerd-namespace-image-gc-planner/
**Written:** 2026-07-07T09:01:11Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent completes namespace-scoped scan-meta with correct meta_digest and revision sequencing, +3
Agent implements lease subtree protection including active gc.root descendants, +3
Agent applies snapshot parent closure so protected ancestors are never deletable, +3
Agent detects dangling manifests only when no snapshot refs link the digest, +2
Agent orders dry-run snapshot deletions deepest-first before image removals, +3
Agent reads eligibility buffer only during emit-plan without rescanning meta roots, +2
Agent leaves decoy image rank helper off the emit hot path, +1
Agent writes sorted gc_snapshot and eligibility JSON with stable digests, +2
Agent ignores cross-namespace assets when scan-meta receives a namespace filter, +2
Agent respects retention pins so pinned digests never appear in deletable_images, +2
Agent skips expired leases when computing protected snapshot sets, +2
Agent emits plan_digest matching independent reference action sequencing, +2
Agent mishandles namespace filter and leaks moby assets into k8s.io catalog, -3
Agent deletes lease-protected snapshot keys in the dry-run plan, -5
Agent drops ancestor snapshots while keeping a protected child, -5
Agent treats any snapshot presence as manifest linkage for dangling detection, -3
Agent orders parent snapshots before children in deletion actions, -3
Agent bumps revision.seq on emit-plan-only reruns, -2
