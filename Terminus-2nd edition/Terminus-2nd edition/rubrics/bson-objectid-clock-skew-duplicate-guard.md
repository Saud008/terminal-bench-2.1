# Platform rubric — bson-objectid-clock-skew-duplicate-guard

**Task folder:** tasks/bson-objectid-clock-skew-duplicate-guard/

Agent binds ObjectId generation to machine_id with a stable five-byte fingerprint, +3
Agent increments the per-second counter for same-second allocation bursts, +3
Agent rejects clock rollback during generation with HTTP 409, +3
Agent rejects per-second counter exhaustion with HTTP 409, +2
Agent round-trips generated _id values through BSON wire encoding, +3
Agent stages ingest-batch-snapshot.json before SQLite export, +3
Agent computes batch_digest using compact-payload separators comma and colon without sorting keys, +3
Agent marks duplicate client_seq without mutating stored payload_json, +3
Agent rejects ingest clock rollback with HTTP 409, +2
Agent exports SQLite rows using snapshot now_unix and document binding, +3
Agent verifies batch_digest during the export commit stage, +2
Agent inserts one document per journal line on the first replay pass, +3
Agent applies zero new inserts when replaying the same journal again, +3
Agent persists replay ledger state across a process restart, +3
Agent scopes applied-line tracking to the journal path being replayed, +3
Agent skips ledger-recorded line numbers after restart before re-inserting, +2
Agent counts only newly inserted lines in the replay applied response, +2
Agent keeps exported Go APIs Generate, NewReplayer, and Replay for isolation overlays, +3
Agent rebuilds wireclock after ObjectId, intake, or journal replay edits, +2
Agent hardcodes ObjectId bytes without machine-bound fingerprint derivation, -3
Agent accepts an earlier now_unix after a later timestamp was generated, -3
Agent re-parses the live HTTP request body during export instead of the snapshot, -3
Agent overwrites payload_json when duplicate client_seq is re-ingested, -3
Agent double-inserts journal lines on repeated replay of the same file, -5
Agent suppresses line numbers globally across unrelated journal paths, -3
Agent renames exported Generate, NewReplayer, or Replay entry points, -3
