# Submission explanations — fit-activity-lap-boundary-decoder

**Task folder:** tasks/fit-activity-lap-boundary-decoder/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task asks agents to implement the Rust fitcore library behind the fitlap CLI so FIT activity streams decode with valid message CRC checks and a two-stage lap export pipeline. Contracts live in five docs under /app/docs and behavior spans CRC, alignment, boundary, trigger, lap time endianness, staging digest, and export from snapshot. The instruction and lap-staging.md document the public Rust API including STAGING_VERSION, LapStaging.source, LapStaging.stem, and export_from_staging(source, stem). Partial implementations pass bundled fixtures but fail when hidden alternate module installs from /opt/verifier-broken-fit exercise export-only or staging-only paths. The shuffle fixture needs start_time ordering for digest and developer notes keyed by original lap index not sorted row position.

## Solution Explanation

The oracle installs golden fitcore modules from solution files, rebuilds fitlap with cargo build, and resets /app/state. Stage one must write /app/state/lap-staging/stem.json before stage two emits export JSON from that file only. Key insight is decode alignment rejection applies on fitlap decode but must not block fitlap laps export, and export must not re-parse the FIT file when staging already holds lap rows. The staging module must expose LapStaging with source and stem fields and export_from_staging must accept those same string identifiers.

## Verification Explanation

test.sh rebuilds fitlap before pytest. Tests call fitlap via subprocess and compare export JSON to an independent reference builder in the test module. Partial alternate module installs from /opt/verifier-broken-fit prove CRC, staging, boundary, digest, and export traps fail independently. Staging path and schema assertions run on catalog and hard fixtures. Module-swap tests import the documented public API only. Oracle patches all golden modules and rebuilds. NOP on the shipped baseline image scores zero.
