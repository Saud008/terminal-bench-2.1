# Platform rubric — go-oci-layer-whiteout-filesystem-materializer

**Task folder:** tasks/go-oci-layer-whiteout-filesystem-materializer/

Agent normalizes tar member paths before staging ledger write, +3
Agent classifies AUFS whiteout and opaque markers during tar ingest, +3
Agent applies whiteout deletion across ordered layer indices, +3
Agent prunes opaque-hidden children from lower layers only, +3
Agent preserves top-layer uid and gid on duplicate paths, +2
Agent materializes overlay-merge.json from tar-member-ledger only, +2
Agent exports filesystem-atlas.json from overlay merge never raw tars, +3
Agent sorts manifest entries before SHA-256 atlas hash, +3
Agent increments ingest-generation replay_seq on each ingest, +2
Agent rebuilds layerfuse after Go source edits, +2
Agent reads whiteout semantics from /app/docs ops contracts, +2
Agent wires hidden verifier fixture stacks under /opt/verifier-fixtures, +2
Agent leaves offpath package off ingest and export hot path, +1
Agent writes manifest hash using canonical JSON line format, +2
Agent skips path normalization and leaves duplicate slashes, -3
Agent treats opaque marker as ordinary file entry, -3
Agent lets lower layer uid win on metadata conflicts, -3
Agent hashes manifest before lexicographic path sort, -3
Agent reads staging ledger during manifest export, -3
Agent ignores whiteout markers and keeps deleted paths, -3
