# FetchContent closure contract

`lib/fetch_closure.sh` is the **only** authoritative source for FetchContent name lists used by `cmake-audit scan`. Scan must not re-derive closure inline from the tree JSON.

## `fetch_collect_names`

Given a parsed tree JSON path, `fetch_collect_names` prints a JSON array of dependency names:

- Collect every `fetchcontent[].name` from **every** file record in the tree (root and nested list files such as `third_party/widget/gadget/CMakeLists.txt`).
- Deduplicate, sort alphabetically, emit JSON (e.g. `["libbar","libbaz","libfoo"]`).

Install manifest `fetch_deps` and `transitive_closure` must both equal this array. Nested subprojects may declare additional entries (e.g. `libbaz` under `third_party/widget/gadget`).

## Scan gate

Before writing the install manifest, `cmake-audit scan` must read `/app/state/hash-audit-snapshot.json` produced by the most recent successful `hash-audit` run:

| snapshot field | requirement |
|----------------|-------------|
| `version` | must be `1` |
| `failures` | must be an empty array |
| `audited_names` | sorted list of dependency names audited in the hash stage |

If the snapshot is missing, unreadable, or `failures` is non-empty, scan must exit non-zero and must not write `--output`.

See `/app/docs/install-manifest-schema.md` and `/app/docs/hash-audit-schema.md`.
