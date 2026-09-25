# CMake tree JSON schema

`cmake-audit parse` writes ingest snapshot `/app/state/cmake-ingest-snapshot.json` then exports a JSON object with:

- `root` — absolute path to the parsed project root.
- `files` — array of CMake list file records sorted by `path`.

Each file record:

| field | type | meaning |
|-------|------|---------|
| `path` | string | project-relative path to `CMakeLists.txt` |
| `list_dir` | string | absolute directory containing the list file |
| `includes` | string[] | project-relative paths from `include()` / `include_guard` loads, sorted |
| `subdirs` | string[] | project-relative paths from `add_subdirectory()`, sorted |
| `fetchcontent` | object[] | FetchContent declarations from `FetchContent_Declare` blocks, in **CMake declaration order** (not sorted by name) |

Include and subdirectory paths resolve relative to the **current list directory**, not `CMAKE_SOURCE_DIR`.
Nested `add_subdirectory()` targets must appear in the tree (e.g. `third_party/widget/gadget`).

## FetchContent entries

Each object in `fetchcontent`:

| subfield | type | meaning |
|----------|------|---------|
| `name` | string | dependency name from `FetchContent_Declare` |
| `url` | string | **archive basename only** (e.g. `libfoo-1.0.0.tar.gz`), **not** the full `file://` URL from CMake. Take the final path segment after the last `/` in the `URL` argument. |
| `url_hash` | string | lowercase hex SHA256 from `URL_HASH SHA256=...` |

Hash audit resolves vendor archives as `<vendor-dir>/<url>` using this basename. Storing the full `file:///app/vendor-cache/...` URL in `url` is incorrect.

## Strict parse mode

With `--strict`, any walked list file that fails syntax validation (unbalanced parentheses, missing `cmake_minimum_required`, or other unrecoverable parse errors) must abort with exit code **2** and must **not** write the output file.

Protected invalid fixtures under `/app/project/bad/` (see `/app/docs/fixture-catalog.md`) exist to exercise strict failure behavior. Do not modify protected fixtures to bypass strict mode.
