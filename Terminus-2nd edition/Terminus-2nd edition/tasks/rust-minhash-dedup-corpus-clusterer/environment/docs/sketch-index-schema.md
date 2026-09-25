# Sketch index schema

Sketch index files are written under /app/state/sketch-index/ minclus scan writes /app/state/sketch-index/<run-id>.json with fields run_id, profile, scan_generation, config_fingerprint, shingle_k, num_hashes, base_seed, and documents array. Each batch run stores one feature embedding sketch per document.

Each document entry includes doc_id, source_path, token_count, shingle_count, and signature array of u64 MinHash embedding rows length num_hashes.

scan_generation starts at one on first scan for a run id. Each rescan of the same run id increments scan_generation by one.

config_fingerprint is the first sixteen hex chars of SHA256 of the string shingle_k colon num_hashes colon base_seed.
