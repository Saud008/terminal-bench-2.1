The expand CLI at /app/cmd/expand reads iCalendar fixtures and writes expanded occurrence rows into SQLite. Current output does not match the published contract.

Make expand --ics … --window … --db … conform to /app/docs/ical-expansion-contract.md and /app/docs/fixture-catalog.md for bundled calendars and procedural inputs used by the verifier.

The environment has no outbound network access. Go is on PATH at /usr/local/go/bin. Rebuild after source changes with:

go build -mod=readonly -o /usr/local/bin/expand ./cmd/expand

Example workflow:

/app/scripts/reset-state.sh
expand --ics /app/fixtures/calendars/weekly-byday.ics --window 2024-01-01T00:00:00Z/2024-03-31T23:59:59Z --db /app/output/weekly.db

Do not edit /app/docs/, /app/fixtures/, or /tests/.
