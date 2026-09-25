# Node class precedence

Hard constraints on ${node.class} must pass before an allocation enters affinity ranking.

Soft affinities on ${node.pool} contribute weight to the raw score before spread penalty adjustment.

Failed hard constraints remove the allocation from placements entirely.

constraint_pass_ok is false when any active allocation violates a hard node.class constraint.
