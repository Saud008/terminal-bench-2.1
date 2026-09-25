# Platform rubric — go-temporal-workflow-history-compaction-inspector

**Task folder:** tasks/go-temporal-workflow-history-compaction-inspector/

Agent sorts workflow history by timestamp_ms then event_id then seq, +3
Agent includes max_run_generation in staging digest per history-staging-schema, +3
Agent resets activity attempt counters at WorkflowExecutionContinuedAsNew, +3
Agent removes cancelled timers from pending lane before risk rollup, +3
Agent increments compaction_seal as one plus continue-as-new boundary count, +3
Agent writes SQLite activity rows sorted by run_generation activity_id attempt, +3
Agent blocks emit-inspect when compaction_seal is zero, +3
Agent emits replay risk rows sorted by run_generation with RETRY_CHAIN code, +2
Agent clears pending timers on TimerFired regardless of fire time delta, +2
Agent produces byte-stable inspection.db on idempotent replay, +2
Agent leaves decoy replayheatmap module off ingest compact emit paths, +1
Agent mishandles equal timestamp_ms ties using seq-only ordering, -3
Agent omits max_run_generation from staging digest canonical payload, -3
Agent carries activity attempt counts across continue-as-new generations, -3
Agent counts cancelled timers as still pending in risk export, -3
Agent exports inspection artifacts without positive compaction seal, -3
Agent retains fired timers in the pending lane after TimerFired, -2
