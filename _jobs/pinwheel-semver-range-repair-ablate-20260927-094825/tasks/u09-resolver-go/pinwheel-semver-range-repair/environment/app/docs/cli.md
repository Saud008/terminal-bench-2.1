# Command line

```
pinwheel satisfies VERSION RANGE
pinwheel compare VERSION VERSION
pinwheel resolve [--registry DIR] PROJECT_DIR
```

Every error is printed to stderr as a single line starting with `pinwheel: `.
Nothing is printed to stdout when a command fails.

## satisfies

Prints `true` or `false` followed by a newline, depending on whether VERSION
satisfies RANGE (see `ranges.md`). Exit status 0 either way.

## compare

Prints `-1`, `0` or `1` followed by a newline when the first version has
lower, equal or higher precedence than the second. Exit status 0.

## resolve

Reads `PROJECT_DIR/pin.json`, resolves it against the registry directory
(`/app/registry` unless `--registry` is given) as described in
`resolution.md`, and writes `PROJECT_DIR/pin.lock` in the format of
`lockfile.md`, replacing any existing lock. On success it prints
`resolved N packages` where N is the number of packages in the lock.

The flag has to come before the project directory.

## Exit status

| status | meaning |
|--------|---------|
| 0 | success |
| 2 | bad usage, invalid version, invalid range, unreadable or invalid `pin.json` or registry file |
| 3 | resolution failed (see `resolution.md`); no lock is written and an existing `pin.lock` is left untouched |

Invalid input is reported as `pinwheel: invalid version "TEXT"` or
`pinwheel: invalid range "TEXT"`.
