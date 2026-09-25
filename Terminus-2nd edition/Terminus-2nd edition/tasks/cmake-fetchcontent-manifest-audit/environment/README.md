# cmake-audit workspace

Offline CMake project under `/app/project` with FetchContent dependencies vendored in `/app/vendor-cache`.
The `cmake-audit` CLI under `/app/bin` scans CMake trees, validates tarball pins, and reports install manifests.

Contract documents live in `/app/docs/`. Run `/app/scripts/reset-state.sh` before audit commands.
