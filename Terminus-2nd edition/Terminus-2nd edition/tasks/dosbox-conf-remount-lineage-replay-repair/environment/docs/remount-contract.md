# Remount lineage contract

`dosbox-plan render` builds a deterministic replay plan from DOSBox-style conf fragments.

## Input

- `--conf-dir` — directory containing fixture conf files and `manifest.txt`
- `--profile` — profile name (bundled fixtures accept `default` only; see `/app/docs/conf-format.md`)
- `--config` — JSON config (see `/app/config/plan.json`)
- `--output` — path for lineage JSON

## Conf processing order

1. Read and join line continuations (backslash at end of line concatenates the next physical line; surrounding whitespace on the continuation is trimmed).
2. Parse sections (`[section]` headers, case-insensitive). Commands are non-empty, non-comment lines inside a section.
3. **Section precedence:** every `[config]` command across all listed conf files is applied before any `[autoexec]` mount replay. Config remaps establish the remap table first; autoexec `mount` / `imgmount` commands are replayed afterward.
4. Within each section type, conf files are processed in manifest order; within each file, commands keep file order.

## Remap directives

In `[config]`:

- `remap_drive OLD NEW` — map drive letter OLD to NEW (letters only, case-insensitive, optional trailing `:` stripped).

Remaps apply to:

- The drive letter argument of `mount` and `imgmount` in `[autoexec]`.
- Paths that begin with `X:` where `X` is a remapped letter (only the leading drive letter is rewritten).

## Mount replay

In `[autoexec]`:

- `mount DRIVE PATH` and `imgmount DRIVE PATH ...` add lineage entries.
- **Stacking:** mounting the same effective drive letter again appends another lineage entry; earlier entries are not removed.
- `imgmount` follows the same remap and stacking rules as `mount`.

## Drive validation

A drive letter is valid when it is exactly one ASCII letter `A`–`Z`. When `fail_on_invalid_drive` is true in config, the first invalid drive in an autoexec `mount` or `imgmount` command fails the render with exit code `2` and appends this exact error string to output `errors`:

```text
invalid drive letter: <DRIVE>
```

`<DRIVE>` is the drive token from the command after optional trailing `:` is stripped and before remap (for example `mount 1 /bad/path` records `invalid drive letter: 1`). Processing stops at the first invalid drive; no further lineage entries are added after that error.

## Exit codes

| Code | Condition |
|------|-----------|
| 0 | Success |
| 1 | Missing conf dir, manifest, config, empty manifest, or a listed conf file |
| 2 | Invalid drive letter on a mount/imgmount command |

Warnings and errors are always written to output JSON even on failure.
