# Platform rubric — rust-gridmesh-portal-playfield-path-planner

**Task folder:** tasks/rust-gridmesh-portal-playfield-path-planner/
**Written:** 2026-07-19T15:45:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent aligns playfield cost, link, and validate modules so validate and path exports match the playtest contracts, +3
Agent accumulates path cost_q16 in integer Q16.16 without float truncation, +3
Agent builds every edge, portal, and off-mesh link in both directions with matching cost_q16, +3
Agent rejects off-mesh endpoints using linear Euclidean snap distance, never squared distance vs linear radius, +3
Agent enforces require_region_match portal region equality and counts islands with 4-connected adjacency only, +2
Agent applies seed-derived off-mesh jump links consistently for both validate and path, +2
Agent rebuilds the release navmeshctl binary before verifier runs, +1
Agent leaves /app/docs, /app/fixtures, and /tests unchanged, +1
Agent fixes only one of cost, link, or validate while the others stay wrong, -3
Agent compares squared snap distance to the linear radius threshold, -3
Agent edits protected fixtures or the verifier reference math under /tests to force a pass, -5
