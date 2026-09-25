# Constraint graph contract

materialize-graph writes constraint-graph.json with graph_fingerprint, nodes, and edges.

Every section with requires_lab true must have a lab_requirement edge to kind lab in edges array.

Fingerprint is sha256 of seed concatenated with sorted section_id bytes.
