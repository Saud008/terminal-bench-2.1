# Platform rubric — cose-sign1-countersign-chain-unwind-repair

**Task folder:** tasks/cose-sign1-countersign-chain-unwind-repair/

Agent aligns cose-audit ingest and export CLI behavior with edited crate source not the unmodified image binary, +2
Agent verifies outer and counter signatures with alg-specific Ed25519 and ES256 paths, +3
Agent unwinds counter-signatures in COSE array creation order not kid lexicographic sort, +3
Agent retains partial chain entries when outer Sign1 verifies but countersign fails, +3
Agent keeps ledger ingest_count at one when re-ingesting identical bundle bytes, +2
Agent writes ingest staging snapshot with canonical protected_key_order per schema, +2
Agent exports chain-manifest unwind traces matching independent reference output, +3
Agent resolves ingest --input basenames under TB3_COSE_DIR for hidden fixture bundles, +2
Agent exits export with status two when SQLite ledger has no ingested rows, +1
Agent leaves wrap.rs counter-sign header rewrap off manifest export hot path, +1
Agent fixes curve verify alone while countersign unwind still sorts by kid not array index, -3
Agent fixes counter-sign order alone while export still drops partial outer_ok chains, -3
Agent fixes staging snapshot alone while ledger re-ingest still increments ingest_count on duplicate bytes, -3
Agent patches wrap.rs expecting manifest unwind changes without export module edits, -2
