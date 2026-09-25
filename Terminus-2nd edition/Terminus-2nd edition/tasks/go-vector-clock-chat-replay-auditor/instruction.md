## Overview

You need an offline chat-timeline admission tool that decides whether moderated room shards may be trusted for sealed audit export on this host. The tool records Lamport vector-clock order, moderation mute intervals, and per-recipient delivery receipts into a local staging ledger, then publishes a sealed JSONL audit timeline only when those records match the site integrity policy. There is no live chat server and no remote download step.

vcreplay at /app/bin/vcreplay is that tool. Operators run load to stage admitted shards, reconcile to enforce causal and moderation authenticity gates, then emit-timeline to publish the sealed audit timeline.

## Operator surface

CLI verbs and fixed verb order live in /app/docs/cli-surface.md.

vcreplay load --room ROOM --scenario SCENARIO must admit numbered NDJSON shards from the active fixture root in numeric sequence order and write the tamper-evident staging ledger at /app/state/chat-staging.json. Load must not write /app/output/audit-timeline.jsonl.

vcreplay reconcile --room ROOM --scenario SCENARIO must read that staging ledger only and write gate findings to /app/work/reconcile-findings.json while bumping reconcile_revision in /app/state/reconcile-revision.json. Reconcile must not publish the sealed timeline.

vcreplay emit-timeline --room ROOM --scenario SCENARIO must read staging and the reconcile revision latch only (never re-scan shard directories) and write the sealed JSONL audit timeline at /app/output/audit-timeline.jsonl. Publish is allowed only after the authenticity pass completes and reconcile_revision is greater than zero.

## Integrity policy

Field-level rules live in the docs below. Reconcile and emit-timeline must enforce every gate before sealing:

- staging snapshot layout and digest binding: /app/docs/chat-staging.md
- Lamport component-wise max and causal authenticity: /app/docs/vector-clock-contract.md
- moderation rank lattice and mute-interval policy: /app/docs/moderation-mute-contract.md and /app/docs/mute-interval-lattice.md
- delivery-receipt authenticity and duplicate suppression: /app/docs/receipt-dedupe-contract.md
- vector-clock gap thresholds and finding codes: /app/docs/gap-findings-contract.md
- sealed timeline schema and reconcile_revision binding: /app/docs/timeline-emit-contract.md

Dup-delivery admissions suppress the lexicographically larger duplicate receipt id. Mod-precedence admissions hide concurrent messages under ban-over-kick policy precedence.

## Paths and fixtures

Bundled room scenarios live under /app/fixtures, including clean-room, mod-precedence, mute-window, dup-delivery, clock-gap, and shard-order. Hidden verifier trees may appear under /opt/verifier-fixtures/vcreplay. Legacy decoy helpers are not on the load, reconcile, or emit integrity path. Do not edit /app/docs/ or /app/fixtures/.
