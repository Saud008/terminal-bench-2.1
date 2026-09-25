# Platform rubric — survey-station-hull-closure-lab

**Task folder:** tasks/survey-station-hull-closure-lab/

Agent implements stationclos bind-lattice and seal-closure on a Rust scientific-computing baseline, +3
Agent writes residual lattice artifacts with monotonic bind_generation, +2
Agent subtracts datum_offset into residual vertices per residual-vector-lemma, +3
Agent quantizes residual corners with toward-zero truncation at microdegree_scale, +3
Agent partitions wrap-crossing rings at absolute longitude delta greater than 180, +2
Agent rejects only positive-area open-interval residual hull conflicts and clears lattice on reject, +2
Agent ranks closure rows by residual_area_u64 ascending then station_id ascending, +2
Agent publishes closure_digest over ranked `id|area|vertex_count` lines matching independent reference math, +2
Agent rebuilds stationclos before pytest and respects microdegree-scale environment overrides, +1
Agent leaves decoy flux index stub off the bind-lattice and seal-closure hot path, +1
Agent replaces only the six domain modules without rewriting unrelated harness files, +2
Agent introduces new failure modes not covered by bundled dual-station-basic fixtures alone, -2
Agent weakens hidden dateline-wrap or micro-scale trap assertions, -3
Agent adds instruction hints naming bug modules or fix steps, -3
Agent copies a three-stage ingest query export pipeline from a neighbor task unchanged, -5
