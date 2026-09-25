# Depot inventory stream format (NUL records)

On this system-administration worktree inventory control plane, each admitted record ends with a NUL byte (0x00). Fields are space-separated unless noted.

## Tag `1` — ordinary changed entry

```
1 <XY> <sub> <mH> <mI> <mW> <hH> <hI> <path>
```

| Field | Meaning |
|-------|---------|
| `XY` | Two-letter index/worktree status |
| `sub` | Submodule state (`N`, `S`, `U`, `?`, `!`, `-`, etc.) |
| `mH` | Octal mode in `HEAD` (`.` if absent) |
| `mI` | Octal mode in index |
| `mW` | Octal mode in worktree |
| `hH` | Object name in `HEAD` |
| `hI` | Object name in index |
| `path` | Path (may contain spaces) |

## Tag `2` — rename or copy

```
2 <XY> <sub> <mH> <mI> <mW> <hH> <hI> <X><score> <newpath><TAB><oldpath>
```

`X` is `R` (rename) or `C` (copy). `<score>` is similarity percentage 0–100.

## Tag `u` — unmerged

```
u <XY> <sub> <m1> <m2> <m3> <mW> <h1> <h2> <h3> <path>
```

| Field | Meaning |
|-------|---------|
| `m1`/`m2`/`m3` | Stage modes (`.` if stage empty) |
| `mW` | Worktree mode (`.` if absent) |
| `h1`/`h2`/`h3` | Stage object names |
| `XY` | Unmerged status pair (e.g. `UU`, `AA`, `DU`) |

## Tag `?` — untracked

```
? <path>
```

## Tag `!` — ignored

```
! <path>
```

## Submodule gitlink

Mode `160000` on any mode field marks a gitlink (submodule):

- Tags `1` and `2`: `mH`, `mI`, `mW`
- Tag `u`: `m1`, `m2`, `m3`, `mW`
