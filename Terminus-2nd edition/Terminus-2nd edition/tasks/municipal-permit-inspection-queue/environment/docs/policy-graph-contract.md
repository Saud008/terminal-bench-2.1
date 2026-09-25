# Policy graph contract

compile-policy writes /app/work/policy-graph.json with lanes map, floors map, and edges list.

Each edge connects permit_type to inspection_lane with direction outbound.

Permit routes table in the database is the authoritative lane source.
