# Hold gate contract

Only objects with `kind` equal to `snapshot` are reclaim candidates.

If a snapshot's `holds` array is non-empty after load-time salt application, that snapshot is blocked with reason `blocked_hold`.

Filesystem holds do not create reclaim candidates; they are irrelevant to eligibility except that filesystems are never eligible.
