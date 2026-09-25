# Auth path trace emit contract

Emit output includes run_id, service, subject, subject_groups sorted lexicographically, steps in execution index order, verdict_code, verdict, reason, trace_digest.

Each step includes index, module, control, result_code, result. The steps array lists every auth module from the ledger service sequence; control-flag short-circuit (requisite failure or sufficient success) freezes the verdict but does not drop later modules from steps. `subject_groups` follows the seeded transitive closure in `/app/docs/group-policy-contract.md`.

trace_digest is sha256 of JSON with service, subject, steps array in index order, and verdict string.
