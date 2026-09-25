# Platform rubric — go-dbt-model-lineage-freshness-sentinel

**Task folder:** tasks/go-dbt-model-lineage-freshness-sentinel/

Agent implements seed-scoped manifest checkpoint ingest with monotonic ingest_seq, +3
Agent evaluates enabled-model DAG traversal excluding disabled nodes, +3
Agent applies source freshness window thresholds with strict greater-than boundaries, +3
Agent computes transitive exposure dependency closure across model edges, +3
Agent persists scan rows with per-seed active replacement semantics in SQLite, +3
Agent emits DISABLED_UPSTREAM alerts when enabled models depend on disabled nodes, +3
Agent exports deterministic alert bundles with canonical audit_digest field ordering, +3
Agent honors TB3_FRESHNESS_BIAS_MINUTES overlay during hidden freshness evaluation, +2
Agent validates seed and bundle against checkpoint before evaluate and export, +2
Agent ignores decoy materializer module outside ingest evaluate export hot path, +1
Agent uses inclusive freshness thresholds that treat boundary minutes as stale, -3
Agent omits disabled upstream alert rows from export bundle, -3
Agent writes shallow exposure refs without transitive model closure, -3
Agent leaves ingest_seq fixed at one across repeated ingests, -3
Agent selects latest scan row without active flag filtering, -3
Agent treats source dependencies as disabled upstream references in summary flag, -3
