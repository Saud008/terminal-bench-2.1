# Platform rubric — clinical-trial-randomization-balance-monitor

**Task folder:** tasks/clinical-trial-randomization-balance-monitor/
**Written:** 2026-07-09T16:30:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent latches trial protocol metadata with deterministic digest via compile-trial, +2
Agent normalizes enrollment NDJSON with ts-then-seq ordering and seq dedupe, +3
Agent builds canonical stratification bucket keys from sorted factor maps, +3
Agent assigns arms from seeded permuted blocks per stratum, +3
Agent counts site enrollment caps using active enrollments only, +3
Agent excludes withdrawn subjects from active balance while keeping history, +3
Agent exports balance-risk JSON with per_stratum counts and max_skew, +3
Agent blocks emit-risk until run-balance sets a positive run_id, +2
Agent rebuilds rtbalctl via session conftest before pytest, +2
Agent passes hidden TB3 site-cap and withdrawal-skew fixtures, +2
Agent sorts sites_at_cap lexicographically in balance export, +2
Agent uses enrollment staging snapshot for export not raw log replay, +3
Agent sorts staging rows by seq before ts, -3
Agent counts withdrawn subjects toward site caps, -3
Agent seeds block permutation from stratum id only ignoring trial id, -3
Agent sums arm gaps instead of absolute max_skew, -3
