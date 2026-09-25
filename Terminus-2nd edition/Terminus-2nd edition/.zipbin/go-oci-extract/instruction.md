Task identity 9946c9ca99 defines the engineering problem for go oci layer whiteout filesystem materializer. See /app/docs/engineering-problem-contract.md for root cause and failure mode contracts.

layerfuse materializes container image layers offline: it walks AUFS-style whiteout markers inside ordered tar archives and emits a sealed filesystem atlas for supply-chain attestation. This is not a live registry pull or Docker unpack; it is a deterministic merge simulator over fixture stacks.

The offpath package at /app/internal/offpath is not consulted during ingest, overlay merge, or manifest publish.

Install the binary at /usr/local/bin/layerfuse from cmd/layerfuse. Required subcommands:

  layerfuse ingest <stack-json>
  layerfuse materialize
  layerfuse manifest export

Ingest reads each layer tar named in the stack manifest and records normalized members in /app/var/layerfuse/tar-member-ledger.json (path, member kind, mode, uid, gid, layer index). Each ingest increments replay_seq in /app/var/layerfuse/ingest-counter.json and records stage_hash.

materialize consumes only the staging ledger and writes /app/var/layerfuse/overlay-merge.json after applying layer precedence, AUFS-style whiteout deletion markers, and opaque-directory hiding.

manifest export reads only the merged layer stack, never raw tar archives, and writes /app/output/filesystem-atlas.json with manifest_hash and replay_seq.

Contracts: /app/docs/aufs-overlay-contract.md, /app/docs/path-normalization.md, /app/docs/ledger-layout.md, /app/docs/whiteout-semantics.md, /app/docs/opaque-directory.md, /app/docs/metadata-precedence.md, /app/docs/manifest-hash.md.

Verifier pytest imports fuse_runtime_helpers and overlay_digest_math. The overlay_digest_math module imports hashlib and tarfile to derive independent atlas hashes from fixture tar archives.

Bundled stacks live under /app/fixtures/oci-stacks: /app/fixtures/oci-stacks/stack.json, /app/fixtures/oci-stacks/layer0.tar, /app/fixtures/oci-stacks/layer1.tar, and /app/fixtures/oci-stacks/layer2.tar. Alternate stacks for hidden evaluation may appear under /opt/verifier-fixtures/oci-layers at runtime.
