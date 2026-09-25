Network prefix operators run the host-local geocur prefix-overlap routing control plane at /app/bin/geocur. Each offline ops pass admits overlapping IPv4 GeoIP and routing-table prefix feeds, applies reserved-range and duplicate-prefix barriers, then publishes a sealed overlap atlas only from committed on-disk feed-cache and ledger state. There is no live GeoIP API or remote routing reflector. This is a system-administration host-local prefix-overlap ops control plane; keep CIDR admission, reserved-range drops, ASN lineage gates, and sealed atlas export aligned. It is not a Rust CLI rebuild, cargo toolchain exercise, pytest harness, or generic service repair exercise.

Ops contracts under /app/docs/ define the enforceable invariants:

- /app/docs/prefix-overlap-ops-contract.md — control-plane overview and ops-validation refresh rules
- /app/docs/feed-cache-schema.md — feed-normalize staging cache fields
- /app/docs/cidr-normalization-contract.md — canonical IPv4 CIDR keys
- /app/docs/duplicate-prefix-precedence.md — feed_id winner selection on shared keys
- /app/docs/reserved-range-policy.md — RFC-reserved prefix drops
- /app/docs/asn-conflict-lineage.md — asn_lineage chains and TB3_ASN_SALT
- /app/docs/overlap-generation-schema.md — overlap-generation ledger row
- /app/docs/atlas-overlap-fields.md — sealed atlas rows, overlap_pairs, audit_digest
- /app/docs/bundle-catalog.md — bundled seed and prefix-bundle inventory

geocur compile-feeds --seed S --bundle NAME must admit a prefix bundle from the active fixture root, normalize CIDR keys, and write /app/state/feed-normalize-cache.json for that seed and bundle.

geocur run-reconcile --seed S --bundle NAME must bind the active overlap-generation ledger row at /app/work/overlap-generation.json from that staging cache under the reserved-range and duplicate-prefix barriers.

geocur emit-overlap --seed S --bundle NAME --output PATH must read on-disk feed-cache and ledger state only and write sealed overlap atlas JSON under /app/output/ at the caller-provided --output path. Field order and digest binding follow /app/docs/atlas-overlap-fields.md. Emit must refuse when seed or bundle gates drift.
Each subcommand accepts --seed and --bundle; emit-overlap also requires --output. Install the binary at /app/bin/geocur from the host-local ops tree under /app. Ops validation refreshes that binary from on-host sources before grading; see /app/docs/prefix-overlap-ops-contract.md. By default, compile-feeds admits bundles from /app/fixtures/bundles/ (or from $TB3_FIXTURE_DIR/bundles/ when that env var is set). Bundled seeds and prefix bundles live under /app/fixtures/. Do not edit /app/docs/, /app/fixtures/, or /tests/.
