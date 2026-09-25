# Demo fixture catalog

Project root: `/app/projects/demo`

| `.la` file | Scenario |
|------------|----------|
| `.libs/libmath.la` | Leaf library, no dependencies |
| `.libs/libutil.la` | Depends on other demo libraries |
| `.libs/libcore.la` | Depends on other demo libraries; `installed=yes` with both libdir and installed_libdir |
| `.libs/liblink.la` | Depends on `libutil`; id sorts before `libutil` but must appear after it in `dependency_order` |
| `.libs/libapp.la` | Aggregator depending on core/link/util/math; duplicate rpath tokens |
| `.libs/liblegacy.la` | Static-only (`old_library`) with `installed=yes` |
| `sub/libhelper.la` | Nested archive with `-L`/`-pthread` noise and a single in-project `-lmath` edge in the shipped tree. `dependency_order` must list **direct** `-l*` targets only (never transitive deps such as `libcore` when only `-lutil` is declared). Copied trees may add more direct `-l*` tokens; still omit transitive ids. |

Shared objects and `liblegacy.a` live beside the `.la` files under `.libs/`. Install-prefix copies live under `install/lib/`.

Linking /app/projects/demo/src/probe.c with -L and -l flags derived from the manifest should resolve libcore.so.0, libutil.so.0, and libmath.so.0 at runtime.

Copied project trees under /tmp/lt-seed-* may include an extra .la whose installed_libdir embeds a seed token.

Hidden verifier trees ship under /opt/verifier-fixtures/. When TB3_LT_PROJECT_ROOT is set to an absolute directory, canonicalize that tree instead of /app/projects/demo for hidden cross-dependency ordering checks.

| Path | Scenario |
|------|----------|
| /opt/verifier-fixtures/lt-cross-dep | libcross lists -lp and -lq while libp depends on libq; dependency_order must be topological not alphabetical |
| /opt/verifier-fixtures/lt-static-only | libarchive is static-only with installed=yes; export must set static_fallback and resolve_dir from installed_libdir |
| /opt/verifier-fixtures/lt-static-only | libarchive is static-only with installed=yes; export must set static_fallback and resolve_dir from installed_libdir |
| /opt/verifier-fixtures/lt-static-only | libarchive is static-only with installed=yes; export must set static_fallback and resolve_dir from installed_libdir |
