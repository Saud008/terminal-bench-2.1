# Submission explanations — nanomsg-surveyor-ballot-deadline-repair

**Task folder:** tasks/nanomsg-surveyor-ballot-deadline-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task is hard because six Go packages under /app/internal/ must cooperate to simulate nanomsg surveyor ballot collection across nine /app/docs contracts before export can succeed. Agents often fix surveyor FSM transitions or header survey-id parsing in isolation while pipe_drained still seals ballots in the wrong order, TTL reconnect windows stay stale, or deadline merge leaves unsealed pending votes inside final_tally. Star topology tally deduplication must collapse duplicate hub edges without double-counting weighted totals, and export must read /app/state/survey-snapshot.json via the staging manifest rather than re-parsing mesh JSON. Partial fixes pass 001-star-complete but fail deadline-partial meshes that require r2 in partial_respondents, hidden reconnect deadline traps, or star double-loop dedup scenarios. A decoy wrap helper under internal/export is off the hot path and cannot substitute for repairing publish, merge, or session logic.

## Solution Explanation

The oracle copies golden implementations into internal/frame/header.go, internal/surveyor/fsm.go, internal/ballot/merge.go, internal/ttl/session.go, internal/topology/dedup.go, and internal/export/publish.go, then rebuilds ballotmesh with go build. Simulate ingests mesh events per mesh-event-format.md, tracks surveyor FSM state, validates 16-byte survey ids at header offset 2, applies TTL expiry and reconnect resets from survey-ttl-reconnect.md, and seals pending votes only when pipe_drained arrives before TTL expiry per ballot-merge-deadline.md. At deadline, final_tally includes sealed votes only while partial_respondents lists still-pending nodes, and star topology weights deduplicate repeated hub edges before computing total_weighted. Export writes /app/output/survey-report.json from the staged snapshot manifest with export_source staging_manifest and honors VERIFIER_TABLE_SUFFIX for table_suffix without reloading fixture files.

## Verification Explanation

Twenty pytest cases compile ballotmesh after every partial-module swap, drive ballotmesh simulate through subprocess on each mesh, and compare JSON output to an independent reference_simulate implementation embedded in the verifier. Five bundled meshes under /app/fixtures/meshes/ cover star completion, pipe-drain sealing order, deadline partial tallies, reconnect TTL refresh, and header survey-id rejection, plus two hidden meshes under /opt/verifier-fixtures for star double-loop dedup and deadline-reconnect interaction traps. Anti-partial-fix tests rebuild with only one golden module patched while the rest stay broken, proving header-only, FSM-only, merge-only, session-only, dedup-only, or publish-only repairs still fail reference checks. Snapshot parity asserts report records match /app/state/survey-snapshot.json, export_source stays staging_manifest, fixture SHA256 integrity is unchanged, and deadline-partial explicitly excludes unsealed r2 from final_tally while listing it under partial_respondents.
