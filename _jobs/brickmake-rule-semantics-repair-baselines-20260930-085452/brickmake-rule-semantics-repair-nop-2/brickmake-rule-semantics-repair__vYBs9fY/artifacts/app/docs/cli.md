# Command line

```
brickmake [options] [NAME=value ...] [target ...]
```

| Option | Meaning |
|---|---|
| `-f FILE`, `--file=FILE`, `--makefile=FILE` | read FILE (may be repeated) |
| `-C DIR`, `--directory=DIR` | change to DIR first; prints `Entering directory` / `Leaving directory` lines unless `-s` |
| `-n`, `--just-print`, `--dry-run`, `--recon` | print recipes without running them |
| `-s`, `--silent`, `--quiet` | do not echo recipe lines |
| `-k`, `--keep-going` | continue after errors |
| `-B`, `--always-make` | treat every target as out of date |
| `-r`, `-R` | accepted for compatibility; brickmake never has built-in rules or variables |
| `-h`, `--help` | usage |
| `-v`, `--version` | version |

Single-letter options can be combined (`-ns`). Arguments containing an
assignment operator (`=`, `:=`, `::=`, `+=`, `?=`) before any other `:` are
command-line variables; see `variables.md`.

## Output

Recipe lines, `$(info)` output, `rm` lines for intermediate files and the
goal messages go to stdout; warnings and errors go to stderr. brickmake's
own messages start with `brickmake:`.

## Exit status

0 on success, 2 on any error (parse errors, `$(error)`, missing rules,
failing recipes). With `-k` the status is 2 if anything failed.
