Our build farm snapshots source trees with gleaner (Rust, source in `/app`) because those machines don't have git, and the snapshots keep disagreeing with what git shows on a developer's machine. Reports so far:

- `build/` in the top-level `.gitignore` only drops the top-level `build` directory, not the ones further down
- a `.gitignore` saved from a Windows editor seems to be ignored completely
- `!keep.tmp` in a subdirectory's `.gitignore` doesn't bring back that directory's `keep.tmp` when the top-level file has `*.tmp`
- a file listed with `!` under a directory that is itself ignored shows up in the snapshot, git leaves it out

There's probably more. gleaner is meant to decide exactly like git: `gleaner list` should print what `git ls-files --others --exclude-standard` prints for an untracked tree, and `gleaner check` what `git check-ignore -v -n` prints. The rules are written down in `/app/docs`; treat those docs as the spec and fix the code, not the docs. It will be run against other trees, patterns and configs than the ones mentioned here.

Keep it plain Rust on the standard library (no dependencies in `/app/Cargo.toml`, no `unsafe` or FFI, and don't run git or any other program from gleaner). Keep the command line and output formats from `/app/docs/cli.md`, and a plain `cargo build --release` in `/app` has to keep working.
