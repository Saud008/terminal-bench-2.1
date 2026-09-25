# CEL trace export

When celctl eval runs with `--trace`, it writes `/app/output/trace.json`:

| Field | Type | Meaning |
|-------|------|---------|
| result | value | Evaluated expression result |
| branches | array | Evaluated branch records |
| has_call_count | integer | Total has() invocations during evaluation |

Each branch record contains `op` (and, or, call, bind), `path` (dot path in AST), and `evaluated` (true). Branches that were short-circuited or pruned must not appear in `branches`. The decoy trace wrapper under internal/decoy is not used for authoritative export.

Trace export reads the staging snapshot only. It must not re-parse the original ingest input.
