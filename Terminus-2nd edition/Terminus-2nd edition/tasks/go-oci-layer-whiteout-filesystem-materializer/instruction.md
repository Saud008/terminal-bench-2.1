Supply-chain auditors run the host-local layerfuse OCI layer filesystem ops control plane at /usr/local/bin/layerfuse. Each offline ops pass admits ordered AUFS-style layer tar stacks from fixture catalogs, stages normalized tar-member ledgers, enforces whiteout deletion and opaque-directory hold gates during overlay merge, then publishes a sealed filesystem atlas only from the merged staging snapshot. There is no live registry pull or Docker unpack. This is a system-administration host-local layerfuse filesystem ops control plane; keep stack admission, whiteout/opaque gates, and sealed atlas export aligned. It is not a generic service repair exercise.

Read the ops contracts under /app/docs/ before changing behavior: ops-failure-envelope.md for the control-plane failure envelope, aufs-overlay-contract.md for ordered merge rules, path-normalization.md for path cleaning before ledger write, ledger-layout.md for staging fields, whiteout-semantics.md and opaque-directory.md for deletion and opaque hold gates, metadata-precedence.md for top-layer uid/gid/mode wins, and manifest-hash.md for sealed atlas hashing.

Install the binary at /usr/local/bin/layerfuse from cmd/layerfuse. Required subcommands:

  layerfuse ingest <stack-json>
  layerfuse materialize
  layerfuse manifest export

layerfuse ingest admits each layer tar named in the stack manifest and records normalized members in /app/var/layerfuse/tar-member-ledger.json (path, member kind, mode, uid, gid, layer index). Each ingest increments replay_seq in /app/var/layerfuse/ingest-counter.json and records stage_hash.

layerfuse materialize consumes only the staging ledger and writes /app/var/layerfuse/overlay-merge.json after applying layer precedence, AUFS-style whiteout deletion markers, and opaque-directory hiding.

layerfuse manifest export reads only the merged layer stack, never raw tar archives, and writes /app/output/filesystem-atlas.json with manifest_hash and replay_seq.

The offpath package at /app/internal/offpath is not consulted during ingest, overlay merge, or manifest publish.

Verifier pytest imports fuse_runtime_helpers and overlay_digest_math. The overlay_digest_math module imports hashlib and tarfile to derive independent atlas hashes from fixture tar archives.

Bundled stacks live under /app/fixtures/oci-stacks: /app/fixtures/oci-stacks/stack.json, /app/fixtures/oci-stacks/layer0.tar, /app/fixtures/oci-stacks/layer1.tar, and /app/fixtures/oci-stacks/layer2.tar. Alternate stacks for hidden evaluation may appear under /opt/verifier-fixtures/oci-layers at runtime. Do not edit /app/docs/, /app/fixtures/, or files under /tests/.
