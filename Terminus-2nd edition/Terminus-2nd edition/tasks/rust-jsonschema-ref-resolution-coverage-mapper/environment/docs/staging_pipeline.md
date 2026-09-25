# Ingest and export pipeline

## Trace

```
jscovmap trace --schema-dir <DIR> --examples <EXAMPLES.jsonl> \\
  --ref-edges /app/state/ref_edges.jsonl \\
  --coverage /app/state/example_coverage.jsonl
```

Each ref_edges line is one JSON object with schema_id, ref_pointer, target_id, status, and optional anchor_name. Lines sort by schema_id then ref_pointer ascending.

Each example_coverage line includes schema_id, example_id (ex-NNN), all_of_branches, and any_of_branches arrays.

example_id values are assigned in file order starting at ex-000 for the first examples line, ex-001 for the second, and so on.

## Bundled fixture identifiers

The bundled validation_examples.jsonl rows use these schema_id and example_id pairs in order:

| Line | schema_id | example_id |
|------|-----------|------------|
| 1 | combo | ex-000 |
| 2 | combo | ex-001 |
| 3 | person | ex-002 |

The bundled schema directory includes person.json and tree.json. With $id URIs ending in person.json and tree.json, ref_edges schema_id values are person and tree respectively per ref_resolution_overview.md.

Environment overrides for hidden grading:

- TB3_SCHEMA_DIR replaces the bundled schema directory
- TB3_EXAMPLES_FILE replaces the bundled examples file

## Publish

```
jscovmap publish --ref-edges /app/state/ref_edges.jsonl \\
  --coverage /app/state/example_coverage.jsonl \\
  --report /app/output/schema_coverage_report.json \\
  --graph /app/output/ref_graph.json
```

totals.resolved_ref_count counts only status resolved. totals.unresolved_ref_count counts status unresolved. totals.recursive_ref_count counts status recursive.

The ref graph lists nodes sorted by id and edges sorted by from, to, ref_kind.
