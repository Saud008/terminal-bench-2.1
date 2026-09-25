# Export manifest format

The output file is UTF-8 text, one row per staged artifact, sorted by path using LC_ALL=C sort on the first column.

Columns are tab-separated without a header row:

```
path	size	sha256	compress	kind	hook_rank
```

- path: relative to rootfs root, forward slashes, no leading ./
- size: byte length of the source file on disk
- sha256: lowercase hex digest of file contents
- compress: compression tag from compression-policy.md
- kind: hook, module, or firmware
- hook_rank: decimal integer per hook-prereq-order.md

When include_hook_scripts is false in stage.json, hook rows are omitted but module and firmware rows remain.

The manifest must be deterministic: repeated runs on the same rootfs and config yield identical bytes.
