# Five-layer step-order audit ladder

Layer 1 topology: breaker endpoints must exist in yard.snapshot adjacency.
Layer 2 energization: recompute after each step per energization-propagation-contract.md.
Layer 3 lockout: reject locked equipment before action.
Layer 4 interlock: apply interlock-constraint-catalog.md using cumulative state.
Layer 5 grouping: audit_digest binds summary counters to ordered step_index list.
