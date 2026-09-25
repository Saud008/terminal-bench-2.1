# AUFS overlay contract for layerfuse

Task token 9946c9ca99 governs how ordered OCI layer tar archives collapse into a single filesystem atlas. This contract is independent of Docker runtime extraction and models only the logical merge used for supply-chain attestation.

Whiteout markers use the AUFS naming scheme. A file named `.wh.<target>` in directory D removes the path D/target from lower layers. The opaque marker `.wh..wh..opq` in directory D hides every child path under D that originated in layers below the opaque marker layer.

Path normalization must run before member classification. Duplicate slashes, dot segments, and missing leading slashes are normalized per path-normalization.md before a tar member enters the tar-member-ledger.

Metadata precedence is strictly top-layer wins for uid, gid, and mode on surviving file and directory entries after whiteout and opaque pruning complete.

The filesystem-atlas manifest hash covers sorted canonical JSON lines. Each line encodes gid, mode, path, type, and uid with four-digit octal mode strings. Hashing occurs only after lexicographic path sort.

The offpath package is compiled but never invoked during ingest, materialize, or manifest export.
