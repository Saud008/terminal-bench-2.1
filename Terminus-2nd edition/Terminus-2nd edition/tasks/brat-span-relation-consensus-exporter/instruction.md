# Bratctl host-local annotation consensus ops desk

Operators run the host-local bratctl annotation-consensus control plane at /usr/local/bin/bratctl. Each offline ops pass admits a multi-annotator BRAT-style project directory, stages a normalized annotation snapshot, applies overlap-resolution, relation-direction, annotator-weight, revision-map, and adjudication-lock gates, then publishes a sealed consensus export only when those gates hold. There is no remote annotation server and no outbound network step. This is a system-administration host-local ops desk (admit → gate → seal). It is not a security product audit, debugging exercise, software-engineering module-repair task, or data-processing pipeline.

bratctl is built from the Go sources under /app. Bring the working baseline under /app (especially packages under /app/internal/) into compliance with the ops contracts below so ingest, consensus, and export match those documents. Evaluation rebuilds /usr/local/bin/bratctl from the sources under /app with go build before grading; replacing only the installed binary without aligning the sources will not pass.

Operators run ingest to admit a project directory, consensus to apply the gates over staged rows, and export to seal the consensus ledger.

## Operator surface

CLI flags and defaults live in /app/docs/cli-surface.md.

bratctl ingest --project <project-dir> must stage /app/state/annotation-stage.json with project identifier, annotator roster with weights, document revision map, revision-normalized annotation rows, project_digest, and a monotonic staging_generation counter under /app/state/staging-seq.json before consensus runs. Only annotators with adjudicator true may declare locks; locks from non-adjudicators must be ignored.

bratctl consensus must read staging only, write /app/state/consensus-generation.json (including the staging_generation and project_digest copied from staging), and refuse sealed export when authenticity gates are unset or drifted.

bratctl export must read consensus-generation and staging metadata only, never re-parsing annotation JSON from the ingest project directory, reject consensus state whose staging_generation or project_digest no longer matches the current staging snapshot, and publish /app/output/consensus-export.json as the sealed consensus ledger.

## Ops contracts

Field-level rules live in the docs below. The desk must enforce every gate before sealing:

- trust admission workflow: /app/docs/trust-admission-workflow.md
- span overlap authenticity gates: /app/docs/overlap-resolution.md
- relation-direction integrity: /app/docs/relation-direction.md
- annotator-weight authenticity: /app/docs/annotator-weighting.md
- revision-map binding: /app/docs/revision-map.md
- adjudication-lock precedence: /app/docs/adjudication-locks.md
- sealed consensus-export attestation schema: /app/docs/consensus-export-schema.md
- fixture catalog: /app/docs/fixture-catalog.md

## Paths and fixtures

Primary artifacts are /app/state/annotation-stage.json (staging after admitted project load), /app/state/consensus-generation.json (gated consensus witness), and /app/output/consensus-export.json (sealed consensus ledger with consensus_digest). Bundled projects live under /app/fixtures/projects/. Do not edit /app/docs/, /app/fixtures/, /app/config/, or anything under /tests/.
