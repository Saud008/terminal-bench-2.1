# Staging schema

hclctl ingest writes /app/state/hcl-stage.json with a fragments array.

Each fragment includes source (basename), order (integer tie-break), block_type, labels (declaration order array), attributes (flat map with dot keys for nesting), dynamics (templates), and merge_overrides.

Fragment order in the array follows lexicographic source filename order during ingest, but each fragment order field is the authority for merge precedence.

Export label ordering: when merging competing label sets across fragments, preserve the label array from the lowest-order fragment. Do not reorder label strings alphabetically for export.

Micro-HCL fragment syntax (one file per fragment):

  order N
  block <type> <label> ...
  attr <key> <value>
  merge <key> <value>
  dynamic { name ... values ... template ... }

Use null for explicit null literals.
