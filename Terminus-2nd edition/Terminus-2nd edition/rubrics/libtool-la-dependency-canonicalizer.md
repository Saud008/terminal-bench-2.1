# Platform rubric — libtool-la-dependency-canonicalizer

**Task folder:** tasks/libtool-la-dependency-canonicalizer/

Agent implements lib-prefixed direct_deps in graph ingest parsing, +3
Agent breaks cycles by lexicographically smallest edge each iteration, +3
Agent writes lt-scan-snapshot.json with snapshot_fingerprint during scan staging, +3
Agent validates snapshot fingerprint before publish export, +2
Agent computes dependency_order via linkorder.sh topological sort not alphabetical, +3
Agent publishes manifest from staged snapshot only without re-walking la files, +2
Agent dedupes rpath tokens preserving first-seen order, +2
Agent resolves installed_libdir when installed=yes for resolve_dir, +2
Agent omits broken cycle edges from dependency_order arrays, +2
Agent ignores decoy_topo.sh legacy preview off publish hot path, +1
Agent patches topo.sh decoy alone leaving linkorder alphabetical, -3
Agent re-walks la files during publish ignoring staged snapshot, -3
Agent emits bare short dependency ids without lib prefix, -2
Agent sorts dependency_order alphabetically instead of topological, -2
Agent skips scan staging leaving publish without snapshot file, -2
