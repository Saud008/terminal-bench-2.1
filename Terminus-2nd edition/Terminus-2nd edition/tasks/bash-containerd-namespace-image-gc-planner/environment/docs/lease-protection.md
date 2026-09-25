# Lease protection semantics

An active lease satisfies expires_at greater than resolve --now.

The label containerd.io/gc.root names a snapshot key. That root and every descendant snapshot in the same namespace must be marked protected and must not appear in deletable_snapshots.
