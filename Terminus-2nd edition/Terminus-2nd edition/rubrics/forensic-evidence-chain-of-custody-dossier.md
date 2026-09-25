# Platform rubric — forensic-evidence-chain-of-custody-dossier

**Task folder:** tasks/forensic-evidence-chain-of-custody-dossier/

Agent preserves officer identifier casing during transfer ingest per custody-transfer-log-format.md, +3
Agent orders lineage edges by event_epoch_ms within each evidence_id, +3
Agent detects seal_break when seal_number differs from expected_seal on transfer rows, +3
Agent rejects non-active storage destinations per storage-location-catalog.md, +3
Agent flags alias_collision when one court_alias maps to multiple evidence ids, +3
Agent requires lab_submit epochs strictly after all transfer epochs for evidence, +3
Agent increments transfer-staging run_seq on repeated ingest for same case bundle, +2
Agent couples evidence-ledger ledger_seq to staging run_seq on reconcile, +2
Agent emits lineage_gap when custody officer hops are discontinuous, +2
Agent sorts broken_chains by evidence_id then code ascending, +2
Agent computes custody_digest including broken_chain id list, +2
Agent honors TB3_CASE_ROOT hidden overlay bundles for seal-break traps, +2
Agent rebuilds cargo release chaindoss before subprocess pytest verification, +2
Agent lowercases officer ids during ingest and breaks lineage matching, -3
Agent sorts lineage edges by event_id instead of chronological epoch, -3
Agent ignores seal mismatch on transfer rows and only checks seal_checks, -3
Agent treats restricted storage locations as valid custody endpoints, -3
Agent reports alias_collision for every alias row instead of true collisions only, -3
