# Platform rubric — s6-rc-longrun-bundle-dependency-state-repair

**Task folder:** tasks/s6-rc-longrun-bundle-dependency-state-repair/
**Written:** 2026-07-19T20:59:13Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent detects hard-dep cycles and exits two from validate with cycle stderr, 3
Agent emits topological plan order that respects hard parents not alphabetical names, 3
Agent marks longruns not-ready while hard parents are down in rc services.json, 3
Agent writes staging.json only after s6-rc mock change with staged_at post-rc, 3
Agent skips duplicate transitions when re-applying the same bundle_id, 3
Agent exports soft edges as from CHILD to PARENT with edge_count matching the edge list, 3
Agent rejects cyclic bundles from export with exit two, 2
Agent records parsed bundle paths in the parser touch file during ingest, 2
Agent keeps ready blocked_by sorted and empty only when all hard parents are up, 2
Agent leaves lib helpers executable after applying dependency and staging fixes, 2
Agent plans services in alphabetical order ignoring hard dependency edges, -3
Agent marks every longrun ready when rc state is empty, -3
Agent writes staging.json before calling s6-rc mock change, -3
Agent exports soft edges with to equal to the literal token soft, -3
Agent omits soft dependencies from export while counting only hard edges, -2
Agent lets validate succeed on the ping-pong cycle fixture, -2
