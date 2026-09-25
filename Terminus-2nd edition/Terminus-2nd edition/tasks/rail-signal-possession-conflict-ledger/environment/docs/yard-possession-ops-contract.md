# Yard possession ops contract

Railpos is the host-local yard possession ops control plane that stages trackgraph witnesses and publishes a sealed conflict ledger for offline safety scheduling.

Primary ops concepts that are unique to this task:

- Undirected track adjacency expands claims into protected zone reachability sets before temporal comparison.
- Maintenance and train windows use half-open minute intervals so abutting endpoints never clash.
- Signal restrict aspects block reservations when protected zones intersect the restricted signal's reach.
- Crisis overrides with priority zero suppress lower-priority claims when override zones intersect claim zones during an overlapping window.
- Conflict rows group participants under stable salted keys and list blocks by kilometer before audit hashing.

Root interaction that makes single-layer patches fail: topology reachability and temporal half-open windows must both agree before a conflict row is emitted.
