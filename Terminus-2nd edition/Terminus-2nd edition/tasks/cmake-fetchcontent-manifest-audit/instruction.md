Offline CMake FetchContent operators run the host-local cmake-audit dependency attestation control plane at /app/bin/cmake-audit. Each offline audit run parses a vendored project under /app/project, verifies vendor-cache digests against pin overlays, and publishes an install-prefix artifact manifest — without network FetchContent downloads. Archives live in /app/vendor-cache, pins in /app/project/overlays/pinned.cmake, and the prebuilt install tree in /app/install. Contracts are in /app/docs/.

Primary artifacts:

  /app/state/cmake-ingest-snapshot.json then /app/data/cmake-tree.json — parse staging then tree export
  /app/state/hash-audit-snapshot.json then /app/data/hash-audit.json — digest admission then sealed hash audit
  /app/output/install-manifest.json — install-prefix scan gated on an empty hash-audit failures array

cmake-audit parse /app/project --output /app/data/cmake-tree.json --strict must persist the ingest snapshot before writing tree JSON matching /app/docs/cmake-tree-schema.md and /app/docs/ingest-snapshot.md. Include and subdirectory paths resolve relative to the current list directory; nested add_subdirectory targets such as third_party/widget/gadget must appear; FetchContent entries stay in declaration order; --strict must exit 2 on the protected malformed fixture under /app/project/bad/ without writing the tree output.

cmake-audit hash-audit --tree /app/data/cmake-tree.json --vendor /app/vendor-cache --pins /app/project/overlays/pinned.cmake --output /app/data/hash-audit.json must match /app/docs/hash-audit-schema.md and /app/docs/fetchcontent-contract.md. Digests hash compressed .tar.gz bytes from the supplied --tree / --vendor / --pins inputs at runtime, read PIN_*_GIT_COMMIT (not GIT_TAG), and write the hash-audit snapshot before the audit JSON. Later stages consume earlier artifacts only and must not re-walk CMake sources.

cmake-audit scan --tree /app/data/cmake-tree.json --prefix /app/install --output /app/output/install-manifest.json must match /app/docs/install-manifest-schema.md and /app/docs/fetch-closure-contract.md: union FetchContent names from every tree file, gate on an empty failures array in the hash snapshot, and record install artifacts including symlink kind with sha256 "-".

Fresh audit runs expect cleared /app/data, /app/state, and /app/output. Do not edit /app/docs/ or protected fixtures under /app/project/bad/.
