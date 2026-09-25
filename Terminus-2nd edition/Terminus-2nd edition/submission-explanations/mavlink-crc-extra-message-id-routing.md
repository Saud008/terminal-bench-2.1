# Submission explanations — mavlink-crc-extra-message-id-routing

**Task folder:** tasks/mavlink-crc-extra-message-id-routing/
**Platform form only** — not in upload zip.
**Updated:** 2026-06-25T18:00:00Z

## Difficulty Explanation

The mavctl CLI decodes MAVLink v2 streams and exports JSON through a decode snapshot at /app/state/decode.snapshot.json. I rated it hard because behavior spans crc-validation.md, checkpoint-replay.md, decode-snapshot.md, and ten rust modules across parse, session, dedup, checkpoint, snapshot, and publish. Fixing CRC or routing alone often passes bundled streams while snapshot payload format, publish ordering, and hidden verifier streams still fail. Agents must serialize payload bytes as JSON integer arrays not hex strings. About 34 behavioral tests include partial-module traps and hidden fixture paths the default catalog never exercises.

## Solution Explanation

The oracle patches mav-core modules in place, copies golden snapshot and publish implementations, rebuilds mavctl with cargo, and drives decode and publish the same way pytest does. Key insight is decode writes the merged frame list to disk before export and publish must read those bytes only. Session seeding on resume, checkpoint-first merge order, and signed GPS decode must all align with the cited docs. Hidden streams under extra fixture directories test dedup and session resume traps independent of bundled catalog names.

## Verification Explanation

test.sh rebuilds mavctl with cargo before pytest. Tests call /usr/local/bin/mavctl via subprocess. reference_replay.py recomputes expected exports from raw streams so pasted JSON cannot pass. Snapshot contract tests assert payload is a JSON byte array. Publish tests mutate snapshot bytes and expect export to follow without re-decode. Partial broken module tests swap single files from verifier storage. Two hidden scenarios read streams from extra fixture directories. NOP on the broken image should score 0.
