# Hash audit schema

`cmake-audit hash-audit` compares FetchContent archives under the `--vendor` directory against pin metadata in the `--pins` overlay and against `URL_HASH` expectations recorded in the `--tree` JSON from parse.

Run `cmake-audit parse ... --strict` before hash audit. Hash audit reads the tree file only—it does not re-parse CMake list files.

Archive lookup uses each dependency's tree `url` field as the tarball **basename** under `--vendor` (see `/app/docs/cmake-tree-schema.md`). The output `archive` field repeats that basename.

Output JSON:

- `deps` — array of dependency records sorted by `name`.
- `failures` — sorted list of dependency names that failed any check.

Each dependency record:

| field | type | meaning |
|-------|------|---------|
| `name` | string | FetchContent dependency name |
| `archive` | string | tarball basename under vendor cache (same as tree `url`) |
| `url_hash_expected` | string | `URL_HASH SHA256=...` from CMake tree |
| `url_hash_actual` | string | SHA256 of the **compressed `.tar.gz` bytes** on disk |
| `pin_field` | string | always `git_commit` |
| `pin_value` | string | value read from the overlay `PIN_<NAME>_GIT_COMMIT` variable for this dependency |
| `ok` | bool | true when actual hash matches expected and pin |

Pin lookup resolves `PIN_<NAME>_GIT_COMMIT` where `<NAME>` is the FetchContent dependency name. CMake variable matching is **case-insensitive**, so `PIN_libfoo_GIT_COMMIT` and `PIN_LIBFOO_GIT_COMMIT` both apply to dependency `libfoo`. Comparisons use the `GIT_COMMIT` pin value, not `GIT_TAG`. Tag strings are informational only.

Tarball digests must be computed on the archive file bytes, not extracted contents.

Implementations must produce correct output for any valid `--tree`, `--vendor`, and `--pins` combination passed at runtime—compute digests from supplied files, never from hardcoded dependency answers.

## Hash audit snapshot (stage staging)

Every successful `hash-audit` run must write `/app/state/hash-audit-snapshot.json` **before** writing `--output`. Scan reads this file; see `/app/docs/fetch-closure-contract.md`.

```json
{
  "version": 1,
  "audited_names": ["libbar", "libbaz", "libfoo"],
  "failures": []
}
```

| field | meaning |
|-------|---------|
| `version` | always `1` |
| `audited_names` | sorted dependency names included in the audit |
| `failures` | sorted names that failed any check (empty when all deps pass) |
