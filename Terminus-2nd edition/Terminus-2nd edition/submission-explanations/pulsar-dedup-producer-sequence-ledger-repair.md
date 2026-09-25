# Submission explanations — pulsar-dedup-producer-sequence-ledger-repair

**Task folder:** tasks/pulsar-dedup-producer-sequence-ledger-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task is hard because pulsar-dedup-replay must reconcile producer|topic stream keying, sliding dedup windows, epoch-gated sequence resets, batch broker-ack filtering, replay duplicate counting, staging snapshots, and broker-ack export barriers across nine /app/docs contracts. Agents often patch stream keying or the dedup window in isolation while epoch reset, batch partial failure, or replay counter logic still diverges from the reference on merged scenarios. Export must persist broker ack state to /app/state/broker-ledger.json and write /app/state/dedup-snapshot.json before emitting /app/output/sequence-ledger-export.json with export_barrier_ok true. Fixing the decoy apply helper in internal/sequence/apply.go does not satisfy export because it is off the replay hot path. Partial module swaps that leave only key.go or counter.go corrected still fail merged and dual-topic checks. The hidden dual-producer trap requires distinct producer|topic partitions when the same producer publishes to two topics.

## Solution Explanation

The oracle installs corrected key.go, window.go, epoch.go, publish.go, counter.go, ledger.go, and run.go, then rebuilds pulsar-dedup-replay with go build -mod=readonly. Replay walks scenario events in order, partitioning ledgers on producer|topic and applying dedup-window, epoch-reset, batch-ack, and duplicate-replay rules before staging. Broker ack maxima are persisted to /app/state/broker-ledger.json and export reads staged snapshot state so high_water never exceeds broker_acked_max per stream. Failed broker_ack events increment dedup_miss without advancing high_water or marking msg_id seen. Replayed msg_id values increment duplicate_replay without touching sequence counters. Export emits tenant, per-stream stats, and export_barrier_ok after the ack barrier completes.

## Verification Explanation

Fifteen pytest functions rebuild the Go binary in test.sh and drive pulsar-dedup-replay export through subprocess on every run. An independent reference_replay module recomputes expected export JSON and staging snapshots from the same scenario fixtures, preventing hard-coded answers. Seven catalog scenarios under /app/fixtures/scenarios/ cover baseline replay, dual-topic keying, window duplicates, epoch reset, batch partial ack, same-id replay, and merged interactions. Tests assert dedup-snapshot.json staging, export_barrier_ok after broker persistence, and CLI exit codes 2 and 3 for missing or malformed scenarios. Hidden dual-producer-trap.json under tests/hidden_fixtures/ fails when topics collapse into one partition. Partial broken-or-fixed module injection proves key-only, counter-only, and decoy apply patches cannot pass export alone.
