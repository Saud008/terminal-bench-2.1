# Job deadline clock

Job deadlines use process time, not broker wall clock.

For each activated job, deadline_ms equals process_clock_ms plus job_timeout_ms from the scenario. Export must set deadline_clock_source to process.

Never derive deadlines from broker_clock_ms even when broker and process clocks diverge in fixtures.
