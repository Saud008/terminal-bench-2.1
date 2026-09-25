# Atlas overlap fields

overlap_rows sorted by country ascending, then asn ascending, then cidr ascending.

Each row includes cidr, country, asn, winning_feed, contained_by (immediate normalized container if any), asn_lineage, reserved_filtered boolean.

summary includes total_prefixes, overlap_pairs (each qualifying unordered pair counted once: different country or asn where one CIDR contains the other), asn_conflicts (rows whose asn_lineage length exceeds one), reserved_dropped.

audit_digest is the lowercase hex SHA-256 of one UTF-8 compact JSON object. Serialization must match Python `json.dumps(payload, sort_keys=True, separators=(",", ":"))` exactly: object keys sorted alphabetically, no spaces after `:` or `,`, and nested arrays emitted the same way.

The payload object has exactly these keys, and the hashed byte string always begins with keys in this order:

1. asn_conflicts
2. asn_lineage_chains (sorted list of each row's asn_lineage array)
3. overlap_pairs
4. reserved_dropped
5. total_prefixes

Canonical shape (values illustrative):

`{"asn_conflicts":1,"asn_lineage_chains":[["a","b"]],"overlap_pairs":2,"reserved_dropped":0,"total_prefixes":3}`

Do not hash pretty-printed JSON, insertion-order key layouts, or a subset of these fields.

asn_lineage values must reflect TB3_ASN_SALT suffix rules from /app/docs/asn-conflict-lineage.md when that variable is set.
