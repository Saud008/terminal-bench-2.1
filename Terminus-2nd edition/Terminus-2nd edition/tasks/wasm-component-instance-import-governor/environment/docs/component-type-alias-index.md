# Type-alias index integrity

Integrity gate for type-index attestation: each admitted import row carries a local type index. A following alias table maps local indices to module-type indices.

Attestation import rows must emit the module-type index when an alias row exists for the local index. Emitting the raw local index when an alias is present is incorrect.

When TB3_TYPE_ALIAS_OFFSET is set, add its unsigned integer value to every module-type index before export.
