# Install manifest schema

`cmake-audit scan` walks `/app/install` and emits JSON describing installed artifacts plus FetchContent closure.

| field | type | meaning |
|-------|------|---------|
| `prefix` | string | install prefix (e.g. `/app/install`) |
| `artifacts` | object[] | `{path, kind, sha256}` sorted by `path`; paths relative to prefix |
| `fetch_deps` | string[] | sorted FetchContent names from `lib/fetch_closure.sh` |
| `transitive_closure` | string[] | **identical** to `fetch_deps` |

Closure name lists come from `fetch_collect_names` in `/app/docs/fetch-closure-contract.md` — do not inline tree walks inside `scan.sh`.

Before emitting the manifest, scan must verify `/app/state/hash-audit-snapshot.json` from hash audit (`failures` empty). Missing or stale snapshots must abort scan with a non-zero exit code.

Only regular files under the prefix are listed; directories are omitted. Symlinks are recorded with `kind: symlink` and `sha256: "-"`.
