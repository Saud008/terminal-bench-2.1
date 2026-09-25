# Requirement rollup contract

Program requirements form a directed acyclic graph. Leaf nodes declare min_credits and allowed course pools or department filters. A leaf is satisfied when matched transcript credits meet min_credits after catalog-year filtering, transfer articulation, substitution mapping, repeat folding, and grade floor rules.

Child requirement satisfaction propagates upward: when a child node is satisfied, its satisfied_credits value rolls up to every ancestor requirement including the root program node. Rollup credits add to direct course matches on parent nodes.

Registrar exception waivers mark a specific requirement satisfied at required_credits without requiring course matches. Waivers do not bypass parent rollup when the waived node has children.

Requirement rows in degree-audit-report.json list req_id, required_credits, satisfied_credits, satisfied boolean, and contributing_course_codes sorted ascending.
