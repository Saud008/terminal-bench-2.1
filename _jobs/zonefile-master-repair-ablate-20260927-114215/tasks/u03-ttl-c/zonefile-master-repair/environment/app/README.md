# zonec

zonec turns DNS master files into a canonical record listing: one fully
qualified record per line, defaults resolved, duplicates removed, sorted in
DNS canonical order. The zone deploy pipeline diffs these listings between
the zone repository and what the authoritative servers serve, so the
listing has to be exact.

Plain C11 with the C library only.

    make                  # builds build/zonec
    make BUILD=/tmp/out   # out-of-tree build
    build/zonec -o example.net examples/example.net.zone

Documentation:

- `docs/zonec.1.md` - command line, exit status, diagnostics
- `docs/master-files.md` - accepted input, directives, default TTLs, includes
- `docs/rdata.md` - supported record types
- `docs/output.md` - listing format and order
- `docs/zonemd.md` - the zone digest (ZONEMD) record

Source layout:

- `src/lexer.c` - entries and tokens
- `src/parser.c`, `src/directives.c` - records and `$` directives
- `src/name.c` - domain names
- `src/ttl.c` - TTL values and defaults
- `src/rdata.c`, `src/rr_*.c` - per-type RDATA parsing and printing
- `src/zone.c` - record store, duplicates, RRset TTLs, ordering, output
- `src/zonemd.c`, `src/sha384.c` - zone digest
