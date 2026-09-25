# Dossier output schema

Published dossier JSON includes case_id, bundle_id, run_seq, evidence_items, lineage_edges, integrity_findings, summary, and custody_digest.

summary counts intact_items, defect_items, seal_breaks, location_invalid, chronology_violation, lineage_gap, alias_collision.

custody_digest is lowercase hex sha256 over deterministic summary and sorted finding ids.
