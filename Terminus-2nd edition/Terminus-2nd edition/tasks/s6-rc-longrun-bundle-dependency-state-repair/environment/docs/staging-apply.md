apply uses plan order and s6_rc_mock.py change to bring services up in the state directory.

Staging snapshot at /app/state/staging.json must be written only after s6-rc change completes successfully. staged_at must be post-rc.

applied.json tracks bundle_id, apply_count, and transitions. Re-applying the same bundle_id without a revision bump must not duplicate transitions or increment apply_count.

Revision is implicit: when bundle_id already exists in applied.json with identical order, apply is a no-op that leaves transition-log.json unchanged.

State directory defaults to /app/state/rc for ready and apply commands.
