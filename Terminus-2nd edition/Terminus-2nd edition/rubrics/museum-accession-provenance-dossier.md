# Platform rubric — museum-accession-provenance-dossier

**Task folder:** tasks/museum-accession-provenance-dossier/
**Form category:** Game (zip `games`; museum accession vault playtest / sealed dossier win-condition)

Agent builds custody lineage from transfer_date succession for the focus accession, 3
Agent detects overlapping exhibition loans and missed return_by windows, 3
Agent applies rights precedence with lower integer winning per restriction level, 3
Agent orders restoration events by event_date ascending for the focus accession, 2
Agent reconciles duplicate accession_id collisions without title-based grouping, 3
Agent increments vault snapshot archive_seq on repeat archive load, 2
Agent keeps archive_seq monotonic across seed/archive changes and rejects corrupt or name-mismatched loads without replacement, 3
Agent publishes dossier JSON with loan and duplicate conflict arrays plus conflict_count, 3
Agent replaces the active dossier row when align runs again for the same seed, 2
Agent binds the active register row to archive_seq and exact snapshot digest, rejecting reloads or byte mutations until realign, 4
Agent rebuilds musdoss after Python source edits, 2
Agent deterministically orders repeated loan flags and same-date restoration/custody rows, 2
Agent uses vault load / compose align / publish dossier hot path without decoy catalog compression, 1
Agent alphabetizes custody parties instead of transfer chronology, -3
Agent drops rights restrictions when precedence ties favor the wrong row, -3
Agent merges duplicate records by object title instead of accession_id, -3
Agent omits loan_conflicts from published dossier export output, -2
Agent sorts restoration timeline newest event first, -2
Agent silently resets a corrupt archive_seq or publishes a stale aligned payload, -3
