# Handler ack order

Handler side effects must record signal acknowledgement in memory **before** any staging snapshot write.

`/app/state/signal-snapshot.json` is written once at the end of replay, after all signal handlers and heartbeat recording finish. Per-signal handler code must not call staging write.

In the **final persisted** snapshot at that path, `staging_written` must be **false**. That field records whether a handler wrote the snapshot file during replay; a correct replay leaves it false because only the end-of-replay persist touches disk. Do not set `staging_written` to true in handler code, and do not flip it to true at final persist.
