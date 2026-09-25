# Platform rubric — warehouse-slotting-replenishment-scheduler

**Task folder:** tasks/warehouse-slotting-replenishment-scheduler/

Agent implements zone-biased SKU velocity scoring with descending rank order, +3
Agent applies slot headroom margin when computing effective pick-face capacity, +3
Agent validates pallet partial picks against min_keep_units remainder rules, +2
Agent binds replen tasks to worker shifts using inclusive shift end minutes, +3
Agent upserts wave_tasks rows so pipeline reruns do not duplicate task_key, +3
Agent gates emit-atlas on wave_latch_pass after crew-bind completes, +2
Agent publishes slot-replen-atlas.json with stable atlas_fingerprint digest, +2
Agent leaves velocity table sorted ascending so high-velocity SKUs rank last, -3
Agent ignores headroom_margin and overfills slots beyond effective capacity, -3
Agent rejects pallet breaks when remainder equals min_keep_units, -2
Agent treats shift_end as exclusive and drops tasks ending on shift boundary, -3
Agent inserts duplicate wave_tasks on every pipeline rerun, -3
Agent emits atlas before crew-bind when wave_latch_pass is zero, -2
