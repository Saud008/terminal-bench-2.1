# Consumer group idle and MKSTREAM semantics

XAUTOCLAIM compares consumer-local idle milliseconds using idle greater than or equal to min_idle_ms. Consumer-local idle is timestamp_ms minus the message last delivery timestamp for the owning consumer.

XGROUP CREATE with MKSTREAM and id dollar sign sets last_id to the tail id of the stream at create time. When the stream already has entries, dollar sign must not collapse to 0-0.

Hidden journals may set TB3_STREAM_PREFIX to rewrite stream key prefixes before replay.
