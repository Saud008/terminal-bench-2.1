# LOS raycast policy

Hex lines are built by a greedy cube-distance walk: from the observer, repeatedly step to a hex neighbor that most reduces cube distance to the target. On ties, choose the neighbor with the smaller `(q, r)` lexicographic pair.

- Endpoints are never treated as blockers.
- A ray is clear when no intermediate cell blocks under the elevation blocker rule.
- `resolve-los` writes one JSONL row per unit×cell pair on the playfield into `/app/work/los-rays/<run-id>.jsonl`.
