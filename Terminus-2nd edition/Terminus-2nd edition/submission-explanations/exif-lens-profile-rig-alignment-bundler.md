# Submission explanations — exif-lens-profile-rig-alignment-bundler

**Task folder:** tasks/exif-lens-profile-rig-alignment-bundler/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task is hard because photogrammetry rig alignment spans ingest staging, EXIF normalization, lens revision selection, checkerboard gates, and export digest validation across eight Bash library modules. Contracts are split across capture-staging.md, exif-timestamp-normalization.md, lens-profile-matching.md, and bundle-manifest-export.md, so fixing only timestamp math or only export still fails hidden TB3 fixtures. Partial fixes pass bundled alpha captures but miss allowed-lens enforcement, missing-frame accounting, or profile revision boundaries at effective_capture_ms. Agents often stop after one lib patch even though twenty-nine behavioral tests require the full ingest-align-export chain and staging snapshot integrity.

## Solution Explanation

The oracle copies corrected shell modules into /app/lib subdirectories for time, lens, gap, rig, checker, and staging, replaces export.sh, runs rebuild-rigbundle.sh, and executes rigbundle ingest, align, and export. The core insight is that align must call each constraint module through the documented bash function surface while export reads only on-disk staging and align-generation artifacts. captures_digest must be sha256 over captures sorted by normalized milliseconds then capture_id, and export must refuse when that digest does not match staging. manifest_digest is sha256 of the bundle JSON body excluding the digest field itself.

## Verification Explanation

Pytest rebuilds shell permissions via rebuild-rigbundle.sh in test.sh, then drives rigbundle through subprocess on every test. An independent reference_bundle.py recomputes normalized timestamps, lens revisions, missing frames, rejections, and manifest fields from the same fixtures cited in instruction.md. Hidden captures under /opt/verifier-fixtures/rig-delta exercise profile revision at effective_capture_ms and full frame-range accounting with different failure modes than bundled alpha data. Parametrized seeds randomize camera serials, lens ids, and timestamps so hard-coded manifest rows cannot pass.
