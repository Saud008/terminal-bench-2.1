# Trust admission workflow

This host-local annotation-consensus ops desk reconciles multi-annotator BRAT-style project directories into a sealed consensus ledger with staging artifacts under `/app/state`. Bring the working baseline under `/app` into compliance so weighted span authenticity, relation-direction integrity, revision-map binding, overlap-resolution, and adjudication-lock precedence match the documented contracts and independent reference ledger math.

The desk has three ops stages tied to documented artifacts:

1. **Ingest** — admit a project directory into `/app/state/annotation-stage.json` with project identity, annotator roster weights, revision map, revision-normalized annotation rows, `project_digest`, and monotonic `staging_generation` under `/app/state/staging-seq.json`. Only adjudicator annotators may declare locks.
2. **Consensus** — read staging only and write `/app/state/consensus-generation.json` applying overlap authenticity, relation direction, annotator weighting, revision offsets, and adjudication lock precedence. Persist `staging_generation` and `project_digest` from staging into the consensus witness.
3. **Export** — combine consensus-generation plus staging metadata into `/app/output/consensus-export.json` with sorted spans, sorted relations, and a canonical `consensus_digest`. Export must reject consensus state whose `staging_generation` or `project_digest` no longer matches staging, and must not re-parse annotation JSON from the ingest project directory.

Reference ledger math must match `/app/docs/overlap-resolution.md`, `/app/docs/relation-direction.md`, `/app/docs/annotator-weighting.md`, `/app/docs/revision-map.md`, `/app/docs/adjudication-locks.md`, and `/app/docs/consensus-export-schema.md`.
