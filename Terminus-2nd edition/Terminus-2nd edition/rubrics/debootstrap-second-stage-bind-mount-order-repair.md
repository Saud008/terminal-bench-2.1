# Platform rubric — debootstrap-second-stage-bind-mount-order-repair

**Task folder:** tasks/debootstrap-second-stage-bind-mount-order-repair/

Agent honors mount-dag after edges and parent path prefix ordering in mount order, +3
Agent places proc and sysfs before bind mounts per mount-dag.md, +3
Agent orders devbind only after proc and devpts after devbind when nested under dev, +3
Agent emits mount_steps records with id source target fstype kind options and omits after, +3
Agent computes gate_digest from sorted canonical mount_count mount_fingerprint snapshot_path JSON, +3
Agent validates gate mount_fingerprint and gate_digest when writing staging manifest, +3
Agent sets staging hooks_ok from actual hook exit codes not a constant true, +3
Agent sets export ok false when any hook exit is non-zero per export-manifest.md, +3
Agent runs chroot hooks only when S2_COMMITTED is set per chroot-hooks.md, +3
Agent seeds resolv.conf under usr/etc when merged_usr is true per resolv-layout.md, +3
Agent idempotently appends one apt suite line when suite_retry reruns sources stage, +2
Agent appends stage2 ledger entry with stage_binding on successful audit runs, +2
Agent patches mount order only while export still reports ok true on hook failures, -3
Agent copies after dependency list from mounts.json into emitted mount_steps records, -3
Agent writes staging manifest with pipeline_version instead of version schema key, -2
Agent seeds resolv under etc when merged_usr layout requires usr/etc path, -3
