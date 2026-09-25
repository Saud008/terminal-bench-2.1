# Relationship-derived features

Relationships are directed keys `"A|B"` → role of A relative to B: `customer`, `provider`, or `peer`.

Valley violation for consecutive triple (A,B,C): hop AB is provider (A is provider of B) and hop BC is customer (B is customer of C) — classic valley. Count each such consecutive pair of hops.

More precisely for hops (A→B) and (B→C):
- valley when A|B = provider AND B|C = customer.

peer→peer transit: A|B = peer AND B|C would also need peer for consecutive… For feature `peer_peer_transit`, flag 1.0 if ANY consecutive hop A|B equals peer.

Unknown edges do not contribute valleys or peer flags.
