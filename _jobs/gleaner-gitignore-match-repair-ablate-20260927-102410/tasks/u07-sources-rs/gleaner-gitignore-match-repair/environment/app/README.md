# gleaner

gleaner lists the files of a work tree that git would not ignore, and
explains why a given path is or isn't ignored, without running git. The
build farm uses it to decide what goes into source snapshots, on machines
that have no git installed.

```
cargo build --release
target/release/gleaner --root /path/to/tree list
target/release/gleaner --root /path/to/tree check build/out.o src/main.rs
```

It is plain Rust on the standard library.

- `docs/cli.md`: commands, output formats, exit status
- `docs/patterns.md`: pattern file syntax and glob matching
- `docs/sources.md`: which files are read and how they are combined

Layout: `src/cli` (argument handling and the two commands), `src/ignore`
(reading pattern files, wildmatch, combining sources), `src/config`
(`.git/config` and the excludes-file location), `src/walk` (tree walk and
output order), `src/report` (output lines).
