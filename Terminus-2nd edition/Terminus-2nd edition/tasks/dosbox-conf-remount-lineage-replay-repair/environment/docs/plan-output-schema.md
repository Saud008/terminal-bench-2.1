# Plan output schema

```json
{
  "plan_version": 1,
  "profile": "default",
  "conf_dir": "/app/fixtures/confs/001-basic-mount",
  "lineage": [
    {
      "seq": 1,
      "op": "mount",
      "drive": "C",
      "path": "/games/demo",
      "source_section": "autoexec",
      "source_file": "game.conf"
    }
  ],
  "remaps": [
    {"from": "D", "to": "E"}
  ],
  "stats": {
    "mount_count": 1,
    "imgmount_count": 0,
    "stack_depth": 1
  },
  "warnings": [],
  "errors": []
}
```

## Fields

- `plan_version` — always `1`
- `profile` — profile name from CLI
- `conf_dir` — absolute conf directory path
- `lineage` — ordered replay entries after config precedence and remaps
  - `seq` — 1-based sequence in replay order
  - `op` — `mount` or `imgmount`
  - `drive` — effective drive letter (single uppercase letter)
  - `path` — host path after remap rewriting of leading `X:`
  - `source_section` — always `autoexec` for lineage entries
  - `source_file` — basename of the conf file containing the command
- `remaps` — config remap directives in application order
- `stats.mount_count` — count of `mount` entries in lineage
- `stats.imgmount_count` — count of `imgmount` entries in lineage
- `stats.stack_depth` — maximum number of lineage entries sharing the same effective drive letter (mount and imgmount counts separately per drive)
- `warnings` — non-fatal strings
- `errors` — fatal strings (present on exit 1 or 2). Invalid-drive failures use the exact format `invalid drive letter: <DRIVE>` where `<DRIVE>` is the parsed mount/imgmount drive token (see `/app/docs/remount-contract.md`).

Keys are sorted when written. Arrays preserve replay order.
