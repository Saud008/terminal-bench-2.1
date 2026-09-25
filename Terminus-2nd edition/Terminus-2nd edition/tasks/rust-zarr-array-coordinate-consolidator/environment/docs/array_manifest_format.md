# Array manifest format

Manifest files live under the manifest directory as JSON files ending in `.array.json`.

Each manifest describes one Zarr-like chunked array:

- `name` — array identifier matching a key in axes.json
- `shape` — full array shape (row-major), two or more dimensions for bundled fixtures
- `chunks` — chunk shape per dimension
- `dtype` — NumPy-style dtype string (for example `<f4`)
- `compressor` — object with `id`, `level`, and `shuffle` integer fields
- `chunk_keys` — list of present chunk indices encoded as `i.j` where `i` is the chunk index along dimension 0 and `j` along dimension 1

The manifest reader ignores `axes.json` in the manifest directory.

Bundled fixtures include array names temperature and pressure under the default manifest directory. Hidden verifier fixtures may add humidity when TB3_MANIFEST_DIR is set.
