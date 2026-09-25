# Task record schema

Each trace JSON file describes one workflow task:

```json
{
  "task_id": "align:sample-A",
  "hash": "ab12...",
  "parent_hashes": ["cd34..."],
  "container": "quay.io/biocontainers/samtools:1.19",
  "container_digest": "sha256:deadbeef...",
  "input_globs": ["inputs/samples/*.fastq"],
  "expansion_hash": "ef56...",
  "attempt": 1,
  "cached": false,
  "exit_status": 0,
  "output_hashes": {"aligned.bam": "sha256:..."},
  "prior_digest": "",
  "prior_exit_status": null
}
```

- parent_hashes lists upstream task content hashes in dependency order (root-first).
- expansion_hash is the SHA-256 hex digest of lexicographically sorted expanded input paths (see run-layout.md).
- lineage_digest is optional; when present ingest admits it as the staged lineage claim for audit to verify.
- prior_digest and prior_exit_status appear on resumed retry rows when attempt is greater than one.
