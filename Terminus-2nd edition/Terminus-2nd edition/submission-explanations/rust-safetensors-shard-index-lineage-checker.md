# Submission explanations — rust-safetensors-shard-index-lineage-checker

**Task folder:** tasks/rust-safetensors-shard-index-lineage-checker/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must reconcile safetensors shard catalogs with binary weight files under interacting layout, digest, dtype, lineage-normalization, journal sequencing, and atlas emission rules. Payload-relative spans, BF16 widths, file-absolute vs payload digests, optional `0x` hash prefixes, globally monotonic `run_seq` across shards, `LINEAGE_ROW` expansion, and tensor-then-code sorting all interact. Case-insensitive compares alone are insufficient. Verifier-only probe catalogs (including overflow reject and multi-violation lineage) are not shipped in the agent image, so partial fixes that look fine on bundled manifests still fail hidden roots.

## Solution Explanation

I rebuilt the release CLI after correcting span gating to payload length, BF16 element width, payload-relative sealing, lineage hash normalization with `0x` stripping, globally monotonic `run_seq`, and atlas emission of `LINEAGE_HASH` plus per-row `LINEAGE_ROW` sorted by tensor then code. The key insight is that `data_offsets` never address the file prefix, fingerprints hash only payload windows, and lineage identity ignores both case and a single optional `0x`/`0X` prefix.

## Verification Explanation

test.sh installs verifier-only probe fixtures, rebuilds xr7, then runs pytest. Contract tests invoke the CLI through subprocess and compare journal and atlas JSON to an independent Python reference. Hidden probe roots exercise corrupt offsets, mixed-case and `0x` lineage hashes, multi-shard sequencing, and multi-violation sort order. Overflow catalogs must fail catalog-scan. NOP on the broken baseline should score zero reward. After the oracle installs patches and rebuilds, all tests should pass.
