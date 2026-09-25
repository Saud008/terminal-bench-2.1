# Platform rubric — yara-match-suppression-window-correlator

**Task folder:** tasks/yara-match-suppression-window-correlator/

Agent ingests YARA events and SOC policy into event-staging.json with events_digest witness, +3
Agent bumps staging-seq.json on each ingest per event-staging contract, +3
Agent applies rule revision windows with inclusive retired_ms boundary, +3
Agent suppresses events on inclusive suppression ticket end_ms, +3
Agent keeps earliest sample_sha256 per asset during hash dedupe, +3
Agent escalates criticality at inclusive escalation_ms through high tier, +3
Agent treats released quarantine after cleared_ms as not suppressed, +3
Agent writes rejected-events.jsonl for events outside active rule revision, +3
Agent refuses export when correlate_generation is zero, +3
Agent validates staging events_digest witness before sealing bundle_digest, +3
Agent rebuilds yaracor from /app before subprocess CLI verification, +2
Agent uses FNV or event_id-only ordering for events_digest, -3
Agent treats suppression end_ms as exclusive at boundary, -3
Agent skips events_digest validation during export seal, -3
Agent pairs hash dedupe on highest detected_ms instead of first seen, -3
Agent treats rule revision retired_ms as exclusive boundary, -3
