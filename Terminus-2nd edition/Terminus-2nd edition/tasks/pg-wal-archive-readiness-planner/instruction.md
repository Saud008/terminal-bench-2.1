Implement the walplan PostgreSQL WAL archive replay readiness planner on the working Bash baseline under /app. The walplan CLI at /app/bin/walplan scans archive directories, ingests a staging snapshot, and emits readiness planner JSON. Libraries under /app/lib implement WAL naming, timeline history parsing, segment continuity checks, partial WAL handling, backup_label parsing, target timestamp selection, staging digest, and planner export.

Build walplan by ensuring /app/bin/walplan and /app/lib modules are executable after edits. Subcommands and flags are defined in /app/docs/cli.md. WAL segment naming and partial suffix rules are in /app/docs/wal-naming.md. backup_label fields are in /app/docs/backup-label.md. Segment end-time math and TB3_CLOCK_ROOT overrides are in /app/docs/segment-clock.md. Staging snapshot schema is in /app/docs/staging-format.md. Planner JSON fields and exit codes are in /app/docs/planner-schema.md. Bundled archive trees are listed in /app/docs/fixture-catalog.md.

Your implementation must satisfy every contract above. The decoy module at /app/lib/decoy/legacy_merge.sh is not on the planner hot path. Planner reasoning combines temporal segment ordering, continuity constraints, and canonical digest hashing over staged segment lists. walplan ingest must write /app/state/wal-archive.stage (or --staging path) before walplan plan reads that snapshot. walplan plan must select replay segments from staging segments_present using segment-clock.json and must not rescan the archive directory for segment lists. Continuity gaps must treat missing segment numbers as gaps. Partial files must not appear in segments_present. Target timestamp selection uses less-than-or-equal segment end times in UTC.

Public workflow:

  walplan ingest --archive ARCHIVE --staging STAGING
  walplan plan --staging STAGING --out PLAN.json --restore-target "YYYY-MM-DD HH:MM:SS UTC"

Hidden verifier fixtures may supply archive trees under /opt/verifier-fixtures/wal-archives/ and alternate segment-clock.json when TB3_CLOCK_ROOT points at /opt/verifier-fixtures/wal-config/. Alternate broken modules may appear under /opt/verifier-broken-walplan/ for partial-path traps.

Do not edit /app/docs/, /app/fixtures/, or /tests/.
