# Platform rubric (games / actplay playtest) — zeebe-bpmn-incident-job-activation-barrier

**Task folder:** tasks/zeebe-bpmn-incident-job-activation-barrier/
**Public CLI:** `/usr/local/bin/actplay`

Agent gates job activation on incident marker persistence per incident-barrier.md, +3
Agent defers boundary events until attached service tasks leave activating window, +3
Agent derives job deadlines from process clock plus timeout, +2
Agent merges incident variable overlays without clobbering output-mapping sources, +3
Agent skips duplicate activations on idempotent replay batches, +3
Agent writes incident-snapshot.json during ingest before export output, +2
Agent keeps staging_written false on final persisted snapshot, +2
Agent exports job-activation-export.json matching reference for catalog scenarios, +3
Agent handles TB3 overlap fixture with barrier and boundary ordering together, +3
Agent handles TB3 overlay trap with dedup skip and protected merge, +3
Agent returns exit code 2 for missing scenario and unknown subcommand, +2
Agent returns exit code 3 for malformed scenario JSON, +2
Agent rebuilds actplay after internal source edits, +2
Agent fixes only deadline clock and leaves incident barrier wrong, -3
Agent fixes only deduper and leaves incident barrier wrong, -3
Agent exports without writing staging snapshot during ingest, -3
Agent ignores output-mapping protection during variable merge, -3
Agent leaves decoy router wrap module on export hot path, -3
