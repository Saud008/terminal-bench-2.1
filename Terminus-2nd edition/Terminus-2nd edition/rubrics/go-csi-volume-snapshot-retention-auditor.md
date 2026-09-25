# Platform rubric — go-csi-volume-snapshot-retention-auditor

**Task folder:** tasks/go-csi-volume-snapshot-retention-auditor/
**Updated:** 2026-07-27T00:00:00Z
Agent joins VolumeSnapshots to PVCs using namespace plus source_pvc composite keys, +3
Agent applies storage class retention_days override when joined PVC class retention is positive, +3
Agent detects dangling snapshots whose source_pvc has no matching PVC in namespace, +3
Agent resolves retention days with Retain flag beating backup policy beating class default, +3
Agent picks highest priority backup policy row matching snapshot namespace selector, +3
Agent sums restore_size_bytes per namespace for quota violation projection, +3
Agent computes k8s fleet graph staging digest with sorted snapshots and pvcs, +2
Agent increments audit_pass_seq counter on score-retention pass, +2
Agent blocks publish-audit until audit_pass_seq is greater than zero, +2
Agent sorts deletable snapshot uids ascending in volsnap audit report, +2
Agent seals report digest over deletable uids protected count and quota violations, +2
Agent honors TB3 fixture directory for hidden policy boundary trap scenario, +2
Agent rebuilds snapretctl via verifier-rebuild.sh before subprocess CLI checks, +2
Agent joins snapshots by PVC name alone ignoring namespace segment, -3
Agent applies cluster default retention before namespace backup policy precedence, -3
Agent publishes volsnap audit report before score-retention increments audit_pass_seq, -3
Agent counts snapshot rows instead of summing restore_size_bytes for quota math, -3
