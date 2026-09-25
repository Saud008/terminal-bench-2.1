# Layered safety audit derivation

Rail possession conflict detection is a five-layer safety audit, not a single reachability pass.

Layer 1 trackgraph: build protected zones from undirected adjacency per trackgraph-zone-contract.md. No temporal data participates in Layer 1.

Layer 2 temporal: evaluate half-open windows per possession-window-contract.md. Only after Layer 1 zones exist, test window overlap and zone intersection jointly.

Layer 3 signal gating: apply signal-aspect-policy.md only to reservations that survived Layer 2 filtering. A restrict aspect blocks movement when the reservation protected zone intersects the signal protected zone.

Layer 4 override suppression: apply crisis-override-precedence.md before pairwise conflict enumeration. Suppressed claims never enter Layer 2 pairwise checks.

Layer 5 grouping: stable lexicographic participant keys per conflict-ledger-emit.md after all prior layers complete.

The control plane requires layers in order. Skipping Layer 1 and comparing raw block_id equality fails on junction layouts.
