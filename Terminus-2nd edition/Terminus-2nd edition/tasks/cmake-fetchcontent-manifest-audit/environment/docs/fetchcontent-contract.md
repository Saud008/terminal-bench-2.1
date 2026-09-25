# FetchContent contract

The demo project under `/app/project` uses offline FetchContent with `file:///app/vendor-cache/<archive>.tar.gz` URLs in CMake list files.

- Root `CMakeLists.txt` includes `/app/project/overlays/pinned.cmake` for audit pins.
- `third_party/widget` fetches `libfoo` and `libbar`.
- `third_party/widget/gadget` fetches `libbaz` (transitive relative to root).
- `/app/vendor-cache/manifest.json` lists archive basenames for reference; hash audit resolves archives from the parsed tree `url` basenames and reads tarball bytes from `--vendor`.

Protected fixtures under `/app/project/bad/` are intentionally invalid. Strict parse behavior for malformed list files is defined in `/app/docs/cmake-tree-schema.md`.

## Audit pipeline

Run stages in order. Later stages read earlier artifacts only—they do not re-walk CMake sources.

1. **Parse** — `cmake-audit parse /app/project --output /app/data/cmake-tree.json --strict` (writes `/app/state/cmake-ingest-snapshot.json` then exports the tree JSON; see `/app/docs/ingest-snapshot.md`)
2. **Hash audit** — `cmake-audit hash-audit --tree /app/data/cmake-tree.json --vendor /app/vendor-cache --pins /app/project/overlays/pinned.cmake --output /app/data/hash-audit.json` (writes `/app/state/hash-audit-snapshot.json`; see `/app/docs/hash-audit-schema.md`)
3. **Scan** — `cmake-audit scan --tree /app/data/cmake-tree.json --prefix /app/install --output /app/output/install-manifest.json` (reads hash snapshot + `lib/fetch_closure.sh`; see `/app/docs/fetch-closure-contract.md`)

Run hash audit before scan in the same session. Scan refuses to run when the hash snapshot is missing or lists failures.

After repairing scan logic, confirm the demo project still builds with `cmake --build /app/build`.

## Ephemeral dependency audits

`hash-audit` accepts arbitrary `--tree`, `--vendor`, and `--pins` paths supplied on the command line. Implementations must compute tarball SHA256 digests and pin comparisons from those inputs at runtime. Do not hardcode expected digests for named dependencies.
