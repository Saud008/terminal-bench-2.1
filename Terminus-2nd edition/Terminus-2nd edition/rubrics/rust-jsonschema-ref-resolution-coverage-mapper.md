# Platform rubric — rust-jsonschema-ref-resolution-coverage-mapper

**Task folder:** tasks/rust-jsonschema-ref-resolution-coverage-mapper/

Agent resolves local file refs using $id basename keys rather than filename stems, 3
Agent indexes JSON Schema anchors with consistent hash-prefixed lookup keys, 3
Agent tracks recursive ref visits by schema_id and pointer pairs not document id alone, 3
Agent records anyOf branch coverage only for branches that match the instance, 3
Agent counts resolved_ref totals from status resolved not raw ref edge row count, 2
Agent sorts ref graph nodes by id and edges by from to ref_kind deterministically, 2
Agent writes trace staging as sorted jsonl ref_edges and example_coverage lines, 2
Agent runs publish export from jsonl staging without re-reading schema inputs, 2
Agent honors TB3 schema and examples overrides during trace ingest, 2
Agent keeps decoy_validate off trace and publish export paths, 1
Agent resolves anchors without the leading hash prefix in the registry, -3
Agent marks every anyOf sibling covered when one branch matches, -3
Agent emits ref graph edges in filesystem discovery order, -2
Agent treats recursive guard as satisfied after first visit to any pointer in a doc, -3
