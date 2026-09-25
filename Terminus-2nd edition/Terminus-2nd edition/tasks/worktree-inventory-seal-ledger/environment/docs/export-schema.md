# Export JSON schema

On this system-administration worktree inventory control plane, sealed atlas JSON uses the fields below.

## Top-level object

| Field | Type | Meaning |
|-------|------|---------|
| `porcelain` | string | Absolute or relative path of input stream |
| `config` | string | Config path used |
| `rename_score_min` | int | Threshold copied from config |
| `entries` | array | Gated entries (see below) |
| `summary` | object | Counts keyed by `kind` |

## Entry object

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `kind` | string | yes | `ordinary`, `rename`, `copy`, `unmerged`, `untracked`, `ignored` |
| `xy` | string | yes | Two-letter status (`..` for untracked/ignored entries) |
| `path` | string | yes | Primary path |
| `old_path` | string | rename/copy | Previous path |
| `score` | int | rename/copy | Similarity score |
| `submodule` | bool | yes | `true` when any mode is `160000` |
| `index_mode` | string | ordinary/rename/copy | `mI` or best available index mode |
| `worktree_mode` | string | ordinary/rename/copy/unmerged | `mW` when present |
| `unmerged_xy` | string | unmerged | `XY` from tag `u` |

## Sorting

`entries` sorted by ascending `path` using UTF-8 byte order.

## Summary keys

Always present (value may be zero):

`ordinary`, `rename`, `copy`, `unmerged`, `untracked`, `ignored`
