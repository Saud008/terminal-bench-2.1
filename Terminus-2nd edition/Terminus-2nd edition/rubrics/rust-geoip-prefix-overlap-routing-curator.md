# Platform rubric — rust-geoip-prefix-overlap-routing-curator

**Task folder:** tasks/rust-geoip-prefix-overlap-routing-curator/

Agent writes feed-normalize staging snapshot at /app/state/feed-normalize-cache.json, +3
Agent persists active overlap-generation row at /app/work/overlap-generation.json, +3
Agent normalizes IPv4 CIDR keys with host bits cleared per cidr-normalization-contract, +3
Agent drops RFC-reserved prefixes before export per reserved-range-policy, +3
Agent picks export winner per normalized prefix key using longest-prefix-precedence, +3
Agent collects distinct asn_lineage ids for every feed sharing a normalized prefix key, +3
Agent suffixes asn_lineage ids with TB3_ASN_SALT before lexicographic ordering when set, +3
Agent names immediate normalized container in contained_by for nested export rows, +2
Agent counts overlap_pairs once per unordered cross-asn or cross-country containment pair, +2
Agent builds audit_digest from summary counters plus sorted asn_lineage chains, +2
Agent sorts overlap_rows by country then asn then cidr ascending, +2
Agent advances reconcile_id when load_generation changes after re-compile, +2
Agent reads staged bytes for emit-overlap instead of re-ingesting raw bundle JSON alone, +2
Agent emits overlap report only to caller-provided path under /app/output/, +1
Agent skips decoy heatmap module on compile reconcile export hot path, +1
Agent uses export-only CIDR fix without compile reconcile salt pipeline for digest trap, -3
Agent omits second feed lineage_id when same normalized prefix appears on multiple feeds, -3
Agent counts overlap_pairs without requiring CIDR containment between rows, -3
Agent drops TB3_ASN_SALT suffix from asn_lineage before audit_digest hashing, -3
Agent picks shorter prefix feed winner when feeds share a normalized prefix key, -3
Agent accepts tampered staging snapshot rows matching independent reference export, -3
