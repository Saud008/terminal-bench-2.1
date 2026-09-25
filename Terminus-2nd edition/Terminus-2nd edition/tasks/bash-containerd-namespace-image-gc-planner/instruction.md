Build ctrgc, a containerd namespace image garbage-collection planner on the working Bash baseline under /app. Cluster operators must publish a deterministic dry-run reclaim plan from namespace metadata, content-store leases, snapshot parent graphs, and image manifests without mutating the backing store.

The baseline ships module stubs under /app/lib and a CLI entry at /app/sbin/ctrgc. Complete scan-meta, resolve, and emit-plan so each stage honors the contracts in /app/docs/cli-contract.md, /app/docs/namespace-scoping.md, /app/docs/lease-protection.md, /app/docs/snapshot-closure.md, /app/docs/dangling-manifests.md, /app/docs/reclaim-sequence.md, /app/docs/gc-snapshot-schema.md, /app/docs/plan-schema.md, and /app/docs/verifier-contract.md.

scan-meta scans a metadata tree and writes /app/state/gc_snapshot.json with a meta_digest. When --namespace is supplied, gc snapshot must include only records belonging to that namespace across namespaces, images, leases, and snapshots. scan-meta advances /app/state/revision.seq only when meta_digest changes.

resolve reads gc_snapshot.json plus a caller-supplied epoch second, evaluates lease protection and retention pins, computes dangling manifests, applies snapshot parent closure to protected sets, and writes /app/state/eligibility.buffer with resolve_digest.

emit-plan reads eligibility.buffer only, emits /app/output/namespace_gc_plan.json in dry-run mode with deletion actions sequenced deepest snapshot first then images by digest, and records plan_digest.

Bundled metadata examples live under /app/fixtures/meta-basic. Verifier-only metadata trees may appear under additional fixture roots not copied in the bundled examples. The optional rank helper in /app/lib/decoy/image_rank.sh is not on the emit hot path. Planner defaults and artifact paths are listed in /app/config/ctrgc.json. The engineering problem contract in /app/docs/engineering-problem-contract.md states the GC safety reasoning agents must implement.
