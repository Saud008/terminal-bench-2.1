# Submission explanations — debootstrap-second-stage-bind-mount-order-repair

**Task folder:** tasks/debootstrap-second-stage-bind-mount-order-repair/
**Platform form only** — not in upload zip.
**Updated:** 2026-06-27T04:19:09Z

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is marked medium because the agent must repair a bash pipeline where ingest, staging, and export disagree unless several layers are fixed together. The contract is split across /app/docs/apt-sources.md, /app/docs/chroot-hooks.md, /app/docs/commit-gate.md, so fixing only parsing or only export math still fails hidden checks. Export must consume the on-disk staging snapshot and manifest digest, not re-walk raw inputs, which is easy to miss when bundled fixtures look fine after a one-file patch. Frontier models tend to stop after the first obvious bug in one module even though 13 behavioral tests require the full contract to line up.

## Solution Explanation

The oracle copies corrected sources (broken sources under /app) into /app, rebuilds the project, and runs the documented CLI end-to-end. The main insight is to keep ingest responsible for merge semantics and snapshot bytes while export derives gaps, fingerprints, and summaries only from that staged artifact. Manifest SHA-256 must match the snapshot file on disk so export validation and pytest staging assertions agree. Exit-code precedence between skipped shards versus timeline gaps must follow the instruction and cli-surface docs, not ad-hoc ordering in emit. Re-running correlate on unchanged inputs should be idempotent because staging and outputs are written through the same code paths agents are expected to fix.

## Verification Explanation

Pytest (13 cases) rebuilds the binary in test.sh, then drives the CLI via subprocess with fresh output paths per test. An independent reference implementation in the test module recomputes expected JSON from the same fixtures and schemas cited in instruction.md, so hard-coded report files cannot pass. Dedicated tests assert the staging snapshot and manifest exist with the ingest contract before export fields are checked. Mutated inputs and byte-level comparisons on reports catch fixes that only work on the default bundle while leaving export or persistence layers broken.
