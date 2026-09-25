# Plan output schema

`/app/lib/export_plan.sh` publishes the sealed plan JSON to the `--output` path
(default `/app/output/plan.json`) only after the staging digest gate passes. The
document is serialized with `indent=2`, `sort_keys=True`, and a trailing newline.

## Fields

```json
{
  "plan_version": 1,
  "manifest_dir": "/app/fixtures/workshop/001-linear",
  "mount_order": ["mod_a", "mod_b", "mod_c"],
  "errors": [],
  "cycles": [],
  "stats": {
    "mod_count": 3,
    "edge_count": 2
  },
  "footer": {
    "run_seq": 1
  }
}
```

- `plan_version` — always `1`.
- `manifest_dir` — the manifest directory passed on the command line.
- `mount_order` — dependency-first mount order; empty on an unresolved cycle.
- `errors` — contract-formatted admission errors in declaration order.
- `cycles` — cycle path strings (`a->b->...->a`) when a cycle is detected.
- `stats.mod_count` — number of `MOD` rows in the staged TSV.
- `stats.edge_count` — number of admitted graph edges.
- `footer.run_seq` — on exit 0, mirrors `seq` persisted in `/app/state/run-seq.json`;
  on failed exits, see Failed runs below.

## Run sequence

`run-seq.json` stores `{"seq": <int>, "input_fingerprint": "<sha256 hex>"}`.
On a successful exit-0 export the fingerprint is compared with the stored value:

- First successful run — `seq` is `1`.
- Same fingerprint — `seq` is unchanged.
- Different fingerprint — `seq` increments by one.

`input_fingerprint` is `sha256(manifest_bytes + b"\n" + canonical_config_json)`
where the config JSON uses sorted keys and compact separators. `run-seq.json` is
only created or updated when the exit code is `0`.

### Failed runs (exit 1 or 2)

Failed exports still seal plan JSON (with errors and/or cycles) and still set
`footer.run_seq`, but they must not persist or increment the sequence:

- No prior `/app/state/run-seq.json` — `footer.run_seq` is `1`; the file remains
  absent.
- Prior `/app/state/run-seq.json` exists — `footer.run_seq` retains the stored
  `seq` as-is; the file contents (including `input_fingerprint`) stay unchanged.
