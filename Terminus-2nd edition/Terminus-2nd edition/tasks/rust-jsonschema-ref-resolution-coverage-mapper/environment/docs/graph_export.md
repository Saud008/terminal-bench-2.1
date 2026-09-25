# Deterministic ref graph export

Nodes include every schema_id and target_id seen in ref_edges. Node kind is schema when the id has no slash after the document key; otherwise definition.

Edges mirror ref resolution with ref_kind equal to the resolution status string.

Export must not depend on filesystem iteration order. Sort nodes by id and edges lexicographically by from, to, then ref_kind before writing ref_graph.json.
