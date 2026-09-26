# shiftclock

Local-time lookups for the rostering service. Handover and on-call times are
stored in UTC; shiftclock turns them into site wall-clock times using the
TZif files in `zones/` rather than the host's tzdata (see `docs/zones.md`).

    go build ./cmd/shiftclock
    ./shiftclock at --zone Europe/Dublin 2031-12-01T09:00:00Z
    ./shiftclock transitions --zone America/Santiago --from 2030 --to 2031

The CLI and its output format are described in `docs/cli.md`.

Layout:

- `cmd/shiftclock` – command line entry point
- `internal/tzif` – TZif reader (RFC 8536): header, data blocks, footer
- `internal/posixtz` – parser and evaluator for footer TZ strings
- `internal/civil` – calendar arithmetic on Unix day numbers
- `internal/report` – JSON line output

Standard library only; `make test` runs the unit tests.
