# NSEC canonical ordering

NSEC owner names in a stub capture must be sorted in DNS canonical order before chain linkage is checked.

Canonical form folds ASCII uppercase letters A through Z to lowercase. Trailing dots are preserved on each owner and next field.

For this stub capture JSON format, sort and compare owner strings bytewise lexicographic order on that folded full-domain string exactly as written in the record (for example hosta.example.com. before hostb.example.com.). This is not RFC 4034 wire-format label order: do not reverse label octets or sort labels right-to-left. Chain validation sorts non-wildcard NSEC records by canonical owner, then requires each record next field to equal the canonical owner of the successor record, wrapping at the zone boundary.

The chain validator must not use raw case-sensitive string order on owner fields. Mixed-case captures such as HOSTA.example.com. and hostb.example.com. sort as hosta.example.com. before hostb.example.com.

Broken chains are reported when any NSEC next owner does not match the canonical successor owner after sorting all NSEC records in the zone.
