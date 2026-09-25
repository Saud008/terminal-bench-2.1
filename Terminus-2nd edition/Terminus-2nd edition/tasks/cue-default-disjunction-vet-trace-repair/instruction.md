Task identity 6e79771b05 defines the engineering problem for cue default disjunction vet trace engine. See /app/docs/engineering-problem-contract.md for root cause and failure mode contracts.

The cuectl CLI must vet and export every workspace listed in /app/fixtures/catalog.json for each seed in /app/fixtures/seeds.json. Workspace scenarios are described in /app/docs/workspace-catalog.md. Vet and export output shapes are defined in /app/docs/vet-trace-schema.md and /app/docs/export-schema.md. The current implementation does not satisfy that contract.

Evaluation is a multi-stage pipeline: stage 1 composes and persists eval snapshots under /app/state/eval-snapshots/, stage 1b validates snapshot invariants, and stage 2 assembles vet/export JSON from the on-disk snapshot only. Stage 2 must not re-run disjunct selection or call EvaluateWorkspace.

Implement the cuewrap Go modules under /app/internal/cuewrap/ so the pipeline satisfies the contracts. /app/internal/cuewrap/diag_linefmt.go is a diagnostic formatter and is not on the export hot path. The module path is github.com/terminus/cuectl. After implementation, cuectl must be installed at /usr/local/bin/cuectl and produce contract-compliant vet and export JSON for the bundled catalog and seeds.

Do not edit /app/docs/, /app/workspaces/, /app/fixtures/, or /tests/.
