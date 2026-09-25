# wtstatus-export contract

On this system-administration worktree inventory control plane, sealed atlas JSON must follow the obligations below.

## Inputs

| Input | Path | Role |
|-------|------|------|
| Inventory stream | --porcelain argument | NUL-delimited depot inventory status bytes |
| Export config | --config argument | JSON with rename_score_min (integer 0–100) |

## Admission obligations

1. Split the input on NUL bytes. Empty chunks after split are ignored.
2. Admit each chunk as one inventory record per /app/docs/inventory-stream-format.md.
3. Tag 2 records are single logical entries: do not decompose the newpath TAB oldpath tail into separate paths.
4. Tag u records are unmerged holds, not ordinary modifications.

## Gitlink hold

When any mode field on a record (mH, mI, mW for tags 1/2; m1, m2, m3, mW for tag u) equals 160000, the atlas entry must set submodule: true.

## Score gating

Read rename_score_min from config. For tag 2 records:

- Read the R score or C score token.
- If score < rename_score_min, drop the record (no atlas entry).
- If score >= rename_score_min, gate as rename (R) or copy (C).

## Export obligations

Write JSON per /app/docs/export-schema.md.

- entries sorted by ascending path (UTF-8 byte order).
- summary counts reflect final gated entries by kind.
- Identical inputs must produce byte-identical atlas JSON (stable key order in objects).

## Protected paths

Agents must not modify /app/docs/, /app/fixtures/, /app/config/export.json, or /tests/.
