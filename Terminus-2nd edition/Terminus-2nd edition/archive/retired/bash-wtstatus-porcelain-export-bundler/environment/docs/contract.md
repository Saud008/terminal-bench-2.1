# wtstatus-export contract

On this build-and-dependency-management status-export bundler, sealed JSON must follow the obligations below.

## Inputs

| Input | Path | Role |
|-------|------|------|
| Porcelain stream | `--porcelain` argument | NUL-delimited `status --porcelain=v2 -z` bytes |
| Export config | `--config` argument | JSON with `rename_score_min` (integer 0–100) |

## Parsing obligations

1. Split the input on NUL bytes. Empty chunks after split are ignored.
2. Parse each chunk as one porcelain v2 record per `/app/docs/porcelain-v2-format.md`.
3. Tag `2` records are single logical entries: do not decompose the `newpath<TAB>oldpath` tail into separate paths.
4. Tag `u` records are unmerged conflicts, not ordinary modifications.

## Submodule detection

When any mode field on a record (`mH`, `mI`, `mW` for tags `1`/`2`; `m1`, `m2`, `m3`, `mW` for tag `u`) equals `160000`, the export entry must set `submodule: true`.

## Score filtering

Read `rename_score_min` from config. For tag `2` records:

- Parse the `R<score>` or `C<score>` token.
- If `score < rename_score_min`, drop the record (no export entry).
- If `score >= rename_score_min`, classify as `rename` (`R`) or `copy` (`C`).

## Export obligations

Write JSON per `/app/docs/export-schema.md`.

- `entries` sorted by ascending `path` (UTF-8 byte order).
- `summary` counts reflect final classified entries by `kind`.
- Identical inputs must produce byte-identical export JSON (stable key order in objects).

## Protected paths

Agents must not modify `/app/docs/`, `/app/fixtures/`, `/app/config/export.json`, or `/tests/`.
