# Platform rubric — bash-ceph-crush-map-placement-explainer

**Task folder:** tasks/bash-ceph-crush-map-placement-explainer/

Agent implements crpe ingest normalize export-ledger pipeline with bucket hierarchy traversal, +3
Agent applies effective osd weight as weight times reweight at ingest without substituting reweight alone, +3
Agent filters down and out osds before normalization denominators and weighted crush_hash picks, +3
Agent preserves pool rule step ordering with take chooseleaf emit witnesses in pg traces, +3
Agent writes normalized fingerprint over eligible osds and ledger_digest per trace ledger schema, +2
Agent exports pg_traces sorted ascending with pg_id hex formatting and primary_osd first acting member, +2
Agent handles TB3 hidden map fixtures with randomized osd ids pool names and reweight multipliers, +3
Agent records chooseleaf excluded_osds witness fields for ineligible osds on each placement step, +2
Agent ignores rack_rank_helper decoy module off ingest export hot path, +1
Agent hardcodes placement ledger JSON without subprocess crpe ingest normalize export-ledger, -3
Agent selects down or out osds in acting_set rows, -5
Agent reorders rule steps placing emit before chooseleaf in trace steps, -3
Agent sorts pg_traces descending by pg_num instead of ascending ledger order, -2
Agent omits normalized snapshot at /app/state/crpe-normalized.json before export-ledger, -2
