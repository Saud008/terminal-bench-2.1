# Submission explanations — fastq-umi-collision-demultiplex-auditor

**Task folder:** tasks/fastq-umi-collision-demultiplex-auditor/
**Platform form only** — not in upload zip.
**Updated:** 2026-06-28T09:39:27Z

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is marked hard because lumidmx ties FASTQ ingest, lane-read staging, demultiplex collision math, and atlas export into one contract spread across five docs under /app/docs/. Lane manifest precedence, paired-read synchronization, UMI canonicalization with mate-specific transforms, and export-only contamination flags each live in different Rust modules, so a single-file patch clears bundled cases while hidden TB3 fixtures still fail. Partial fixes such as correcting barcode Hamming without R2 reverse-complement rotation, or building clusters without lex-min cluster_id, pass some pytest cases but break reference cross-checks and digest bytes. Agents often treat decoy helpers or raw FASTQ re-parsing as shortcuts even though export must read only the staged ledger paths. The interacting behaviors mean roughly six modules must agree before all twenty-eight behavioral tests and five hidden-trap cases pass together.

## Solution Explanation

The oracle copies six corrected Rust modules into /app, rebuilds lumidmx, and runs stage ingest, demux run, and atlas export in order. The core insight is that ingest writes the authoritative lane-read staging snapshot while demux consumes synced pairs only and writes the UMI demux ledger that export reads without touching FASTQ again. Lane-first precedence merges overrides into effective barcodes before Hamming assignment, and UMI canonicalization applies reverse-complement on R2 before the shared rotate-left seed shift including TB3_UMI_SEED_SHIFT. Collision families use the lexicographically smallest canonical UMI as cluster_id, and atlas export adds cross_sample contamination flags when one canonical UMI maps to multiple sample_ids. Re-running demux or export on unchanged staging should remain idempotent because generation counters and digest hashing follow the atlas-export-ledger contract.

## Verification Explanation

Pytest runs twenty-eight behavioral cases after test.sh rebuilds lumidmx via cargo and copies the binary to /app/bin. Every test drives the CLI through subprocess with fresh state paths, and reference_demux.py independently recomputes staging, ledger entries, clusters, contamination flags, and SHA-256 digest from the same JSON contracts. Bundled FASTQ fixtures under /app/data/reads exercise lane overrides, N-tolerant barcode matching, and multi-sample collision clustering, while tests also assert staging fields loaded from /app/data/lanes.json. Hidden verifier fixtures under /opt/verifier-fixtures/lumidmx supply random sample ids, shifted UMI seeds via TB3_UMI_SEED_SHIFT, and cross-sample contamination that bundled data alone cannot satisfy. Restart and idempotency checks plus byte-level digest comparisons catch export-only or staging-skipping shortcuts that would not survive a second atlas export.
