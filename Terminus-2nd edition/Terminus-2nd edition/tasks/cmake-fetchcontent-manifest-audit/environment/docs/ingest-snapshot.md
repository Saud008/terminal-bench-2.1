# CMake ingest snapshot (stage 1)

`cmake-audit parse` is a **two-stage** pipeline:

| Stage | Module | Output |
|-------|--------|--------|
| 1 Ingest | `lib/ingest.sh` | `/app/state/cmake-ingest-snapshot.json` |
| 2 Export | `lib/export_tree.sh` | final tree JSON via `--output` |

Stage 2 must read the ingest snapshot only — it must **not** re-walk CMake list files on disk.

## Snapshot schema (version 1)

```json
{
  "version": 1,
  "root": "/app/project",
  "files": [
    {
      "path": "CMakeLists.txt",
      "list_dir": "/app/project",
      "includes_raw": ["overlays/pinned.cmake"],
      "subdirs_raw": ["third_party/widget", "src"],
      "fetchcontent": []
    }
  ]
}
```

| Field | Meaning |
|-------|---------|
| `version` | Always `1` |
| `root` | Absolute parsed project root |
| `files` | Records in breadth-first queue pop order (see BFS walk below) |
| `includes_raw` | Project-relative include paths in **CMake line encounter order** before export dedupe/sort |
| `subdirs_raw` | Project-relative subdirectory paths in **CMake line encounter order** before export dedupe/sort |
| `fetchcontent` | FetchContent entries in **CMake declaration order** (never re-sorted by name) |

## BFS walk (stage 1)

Discovery uses a breadth-first queue starting with `CMakeLists.txt`:

1. Pop the front path from the queue; skip if already visited.
2. Read the list file and append one record to `files` in pop order.
3. Enqueue child list files as `{subdir}/CMakeLists.txt` for each path in **`sorted(set(subdirs_raw))`** — dedupe within the current file, then enqueue in **alphabetical** order.

`includes_raw` and `subdirs_raw` on each record preserve **CMake encounter order** (line order in the list file). Only the BFS **enqueue order** uses sorted subdirectory paths; do not enqueue in declaration order.

Export stage writes `/app/data/cmake-tree.json` per `/app/docs/cmake-tree-schema.md`: dedupe and sort `includes_raw` → `includes`, dedupe and sort `subdirs_raw` → `subdirs`, copy `fetchcontent` verbatim.

See also `/app/docs/fetchcontent-contract.md` and `/app/docs/cmake-tree-schema.md`.
