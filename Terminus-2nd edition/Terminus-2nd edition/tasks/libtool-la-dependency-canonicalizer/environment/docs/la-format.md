# Libtool `.la` archive format (canonicalizer profile)

Each `.la` file is a libtool-style text archive. The canonicalizer reads these fields:

| Field | Meaning |
|-------|---------|
| `dlname` | Shared object soname when building shared libraries (may be empty) |
| `library_names` | Space-separated shared file names (may be empty) |
| `old_library` | Static archive name when no shared object is exported |
| `installed` | `yes` or `no` |
| `libdir` | Build-tree library directory |
| `installed_libdir` | Install-prefix library directory (present when `installed=yes`) |
| `dependency_libs` | Linker tokens such as `-lutil -lmath` referencing other `.la` bases in the same project |
| `rpath` | Space-separated runtime search directories (may contain duplicates) |

Blank lines and `#` comments are ignored. Values are single-quoted strings on each line.

## Path resolution

When `installed=yes` and `installed_libdir` is non-empty, `resolve_dir` must be `installed_libdir`. Otherwise use `libdir`.

## Dependency ordering

For each library, `dependency_order` includes **only direct** in-project dependencies parsed from `dependency_libs` (depth 1). Do **not** walk transitive dependencies: if `libhelper` lists `-lutil` and `libutil` depends on `libcore`, `libhelper` must **not** include `libcore` in `dependency_order`.

Build a directed graph on that direct edge set and emit those ids in **topological** order (dependencies before dependents within the set). Only count edges between ids that are both in the library's direct dependency list.

When several ids are ready to emit at once during topological sort, take the **lexicographically smallest** id first (UTF-8 / `LC_ALL=C` string order). After each emission, resort the pending ready set the same way. Never replace topological ordering by sorting the full direct dependency list alphabetically.

Example: if `libhelper` lists `-lmath -lutil`, then `dependency_order` is `["libmath", "libutil"]` even though `libutil` depends on `libcore` elsewhere in the project.

## Kahn topological sort (direct subgraph)

Work on the **direct dependency subgraph** for library `L`: start with the ids listed in `L`'s `dependency_libs` that match other `.la` files in the project. Ignore transitive deps outside that set.

**Edge direction (in-degree):** when library `X` lists `-lY`, `X` **depends on** `Y`. Treat that as a directed edge `X → Y` for sorting purposes: `Y` must appear before `X` in `dependency_order`. The in-degree of `X` counts how many **remaining** direct dependencies (within the subgraph) `X` still waits on.

**Cycle breaks:** skip any edge recorded in `broken_edges` when computing in-degrees and when relaxing edges after an emission. When the direct edge `L → D` is in `broken_edges`, **omit `D` from `L`'s `dependency_order` entirely** — do not list it as a pending node, do not emit it later, and do not treat it as a transitive placeholder. Broken dependencies are absent from the array, not merely reordered.

After the demo cycle break removes `libcore → libutil`, `libcore`'s only direct in-project dependency was that edge, so **`libcore.dependency_order` is `[]`**. `libutil` still lists `libcore` in its own `dependency_order` because `libutil → libcore` was not broken.

Worked example for `libapp` with direct deps `{libcore, liblink, libutil, libmath}` after the project-wide cycle break removed `libcore → libutil`:

| Library | Direct deps within subgraph |
|---------|----------------------------|
| `libcore` | `libutil` (removed by cycle break — ignore) |
| `liblink` | `libutil` |
| `libutil` | `libcore`, `libmath` |
| `libmath` | (none) |

Initial in-degrees: `libcore=0`, `libmath=0`, `libutil=2`, `liblink=1`.

1. Ready set `{libcore, libmath}` → emit **`libcore`** (lexicographically smallest). Relax edges into dependents: `libutil` waits on one fewer → in-degree `1`.
2. Ready `{libmath}` → emit **`libmath`**. Relax: `libutil` in-degree `0`.
3. Ready `{libutil}` → emit **`libutil`**. Relax: `liblink` in-degree `0`.
4. Ready `{liblink}` → emit **`liblink`**.

Result: `["libcore", "libmath", "libutil", "liblink"]`. Re-sort the ready set lexicographically after each emission; do not replace this process with a single alphabetical sort of all direct deps.

## Cycles

When the graph contains a cycle, do **not** abort. Repeatedly break cycles until the graph is acyclic.

Each iteration:

1. Consider every remaining directed edge `(from,to)` where `from` lists `-lto` in `dependency_libs`.
2. An edge is a **cycle edge** when `to` can reach `from` again using only remaining edges (skip edges already in `broken_edges`).
3. Collect **all** cycle edges present in the current graph (including when multiple disjoint cycles exist).
4. Remove the edge whose key `from/to` is **lexicographically smallest** (UTF-8 / `LC_ALL=C` string order).
5. Append that edge to `broken_edges` and repeat.

Do **not** stop after the first cycle found by a single walk; the smallest edge must be chosen across every cycle edge in the graph for that iteration.

Example with two independent 2-cycles `libm ↔ libn` and `libx ↔ liby` in the same project: the first iteration sees cycle edges `libm/libn`, `libn/libm`, `libx/liby`, and `liby/libx`; the smallest is `libm/libn`. After removing it, the next iteration breaks `libx/liby`, yielding `broken_edges` `[{"from":"libm","to":"libn"},{"from":"libx","to":"liby"}]`.

## Rpath deduplication

For each library, dedupe `rpath` entries preserving **first occurrence** order. Do not sort rpath entries.

## Static vs shared merge

When `dlname` is empty and `old_library` is non-empty, set `static_fallback` to `old_library` and leave `shared_name` empty. When `dlname` is set, `shared_name` must be `dlname` and `static_fallback` empty.

## dependency_libs parsing

`dependency_libs` may include linker flags that are not library names (`-L`, `-R`, `-pthread`, and similar). Ignore those tokens.

For each `-lNAME` token, form graph id `libNAME`. Include the edge only when `libNAME` matches the basename of another discovered `.la` file in the same project walk.

## Discovery

Recursively find `*.la` under the project root. Sort by relative POSIX path ascending before processing.
