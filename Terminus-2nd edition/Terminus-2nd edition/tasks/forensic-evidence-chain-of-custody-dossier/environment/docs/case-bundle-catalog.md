# Case bundle catalog

Bundled fixtures: metro-gun-chain, seal-break-trap, lab-order-trap, alias-collision-trap, lineage-gap-trap.

metro-gun-chain uses case_id CASE-METRO-441 and evidence_id EVD-7F2A in bundled fixtures.

seal-break-trap uses case_id CASE-METRO-442.
lab-order-trap uses case_id CASE-METRO-443.
alias-collision-trap uses case_id CASE-METRO-444.
lineage-gap-trap uses case_id CASE-METRO-445.

Hidden verifier overlay bundles live under /opt/verifier-fixtures/forensic/cases with case_id CASE-HIDDEN-901 and bundle hidden-seal-overlay.

Guard replay tests may materialize a randomized bundle as rand-chain.json under a temp TB3_CASE_ROOT and write dossier output named with the -rand-chain-dossier.json suffix (for example CASE-METRO-441-rand-chain-dossier.json).
