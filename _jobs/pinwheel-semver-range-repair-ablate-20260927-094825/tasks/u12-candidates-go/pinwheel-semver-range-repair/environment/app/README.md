# pinwheel

pinwheel resolves a project's `pin.json` against a directory-based package
registry and writes a flat `pin.lock` next to it. The version and range logic
it uses is also exposed on the command line, which is handy when you want to
know why a range did or didn't pick something.

    go build -o /usr/local/bin/pinwheel ./cmd/pinwheel
    pinwheel resolve examples/storefront

## Layout

- `cmd/pinwheel` - entry point
- `internal/cli` - subcommands and exit codes
- `internal/semver` - version parsing and precedence
- `internal/semrange` - range parsing and matching
- `internal/registry`, `internal/manifest` - input files
- `internal/resolve` - resolution rounds and release choice
- `internal/lockfile` - `pin.lock` output
- `registry/` - registry snapshot used when `--registry` is not given
- `examples/` - sample projects

## Docs

- `docs/cli.md` - commands, output, exit codes
- `docs/ranges.md` - version and range syntax
- `docs/resolution.md` - how a lock is computed
- `docs/lockfile.md` - `pin.lock` format
- `docs/registry.md` - registry and manifest files
