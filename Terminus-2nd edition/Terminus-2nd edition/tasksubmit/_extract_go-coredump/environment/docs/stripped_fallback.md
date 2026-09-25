# Stripped binary catalog trust fallback

The trusted catalog at `/app/fixtures/catalog/build_index.json` maps authenticity build IDs to symbol metadata.

When the mapped ELF is marked `stripped: true`:

1. Try `debug_path` from the catalog entry for the admitted build ID (companion authenticity file path).
2. If absent, try `<binary_dir>/.debug/<basename>` under the mapped binary directory.
3. Resolve frame authenticity from the companion ELF using the file-relative offset.

Non-stripped binaries resolve frames directly from the mapped file catalog entry.
