# Corpus catalog

Bundled JSONL training batches under /app/fixtures/corpora/ exercise feature sketch scan, similarity eval grouping, and dedup attest export.

near-duplicates-basic contains two near duplicate news sentences and one unrelated line. unicode-punct-mix contains NFKC-heavy text with a normalized duplicate pair. shingle-boundary tests exact k token windows. threshold-edge places three documents near the default floor. multi-cluster contains two duplicate pairs plus one singleton.

Profiles in /app/fixtures/run_profiles.json name default strict and relaxed jaccard_floor presets. scan records the profile name in the sketch index.
