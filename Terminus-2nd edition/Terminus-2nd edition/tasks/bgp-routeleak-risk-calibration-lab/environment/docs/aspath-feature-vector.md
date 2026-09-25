# AS-path feature vector

Feature order (must match model.json feature_names):

1. `path_len` — number of ASNs in as_path.
2. `origin_asn` — last ASN in as_path (origin).
3. `private_origin` — 1.0 if origin is RFC1918-like private ASN in [64512, 65534], else 0.0.
4. `reserved_hop` — 1.0 if any hop (including origin) is in reserved documentation range [64496, 64511], else 0.0.
5. `unique_asn_ratio` — distinct ASN count / path_len (1.0 for empty path treated as 0 path → 0.0).
6. `valley_count` — count of provider→customer→provider valley violations along consecutive relationships (see relationship-features.md).
7. `peer_peer_transit` — 1.0 if any consecutive pair is peer→peer (forbidden transit), else 0.0.
8. `first_hop_customer` — when len>=2, 1.0 if as_path[0] is a customer of as_path[1] according to their directed relationship; otherwise 0.0. If len<2 → 0.0.

Missing relationships for a consecutive pair count as neither valley nor peer-peer (treated as unknown, no flag).
