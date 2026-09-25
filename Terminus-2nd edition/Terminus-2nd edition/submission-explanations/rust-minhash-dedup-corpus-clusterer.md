# Submission explanations — rust-minhash-dedup-corpus-clusterer

**Task folder:** tasks/rust-minhash-dedup-corpus-clusterer/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Humans and agents struggle because MinHash dedup spans normalization, shingle windows, seed mixing, threshold clustering, and provenance digests across interacting Rust modules. A single obvious edit can pass bundled batches yet still fail hidden salt traps or rescan generation checks. Partial fixes that touch only scan or only export leave audit_digest or cluster_run_id inconsistent across runs.

## Solution Explanation

I traced each failing contract to its module and corrected normalization, shingle stride, seed mixing, and Jaccard thresholding. Union-find grouping and audit_digest canonical JSON were aligned with the schema docs. Rebuilding minclus fixed the scan, group, and attest pipeline so eval report fields stay consistent.

## Verification Explanation

Pytest rebuilds minclus before each run and drives the CLI through subprocess calls. minhash_ref recomputes cluster graphs independently from fixture JSONL. Hidden corpora under extra fixture directories catch shallow one-file patches.
