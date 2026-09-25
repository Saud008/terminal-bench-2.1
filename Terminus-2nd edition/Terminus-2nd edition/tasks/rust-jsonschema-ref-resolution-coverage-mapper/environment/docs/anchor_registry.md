# Anchor registry contract

During ingest, each schema document builds an anchor map from $anchor values encountered in subschemas.

Lookup keys in the internal map store the anchor name without a leading hash. A $ref value of #PetAnchor resolves when some subschema under the same document declares "$anchor": "PetAnchor".

Cross-file anchor refs use a relative file path plus fragment, for example common.json#SharedAnchor.

Resolved anchor edges must set anchor_name to the bare anchor token and status to resolved.
