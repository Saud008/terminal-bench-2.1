# DN normalization

All distinguished names are normalized before comparison. RDN attribute types are lowercased. Surrounding whitespace on each RDN component is trimmed. Multi-valued RDN order is preserved left-to-right as written in LDIF.

Normalized DNs appear in staging snapshots and matrix decisions.
