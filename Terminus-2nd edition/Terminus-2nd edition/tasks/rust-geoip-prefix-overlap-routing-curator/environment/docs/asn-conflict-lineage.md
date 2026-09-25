# ASN conflict lineage

When the same normalized CIDR appears on multiple feeds, asn_lineage must list every distinct lineage_id from those feeds in lexicographic order, even when the ASN values match.

When the TB3_ASN_SALT environment variable is set, append its string value to each lineage_id before sorting and deduplicating asn_lineage for emit-overlap and audit_digest hashing. When unset or empty, write raw lineage_id values without a suffix.

summary.asn_conflicts counts atlas rows whose asn_lineage length exceeds one.
