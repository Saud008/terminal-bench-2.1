Build the glyph-sheet atlas playtest packer, a Rust offline sprite packing CLI for 2D playfield glyph sheets on the working baseline under /app. The packer loads catalog fixtures, packs padded UV bleed atlases, emits checksum manifests, and probes edge UV samples so playtest sealing matches the packing contracts.

Authoritative contracts define correct behavior: /app/docs/atlas-contract.md for padding, bleed replication, UV rectangles, rotation, duplicate frames, seed scaling, and size limits; /app/docs/manifest-schema.md for manifest fields and checksum canonicalization; /app/docs/exit-codes.md for pack and probe exit obligations.

atlaspack pack accepts --catalog, --sprites, --set, --seed, --atlas-out, and --manifest-out. It must write a PNG atlas and JSON manifest that honor those contracts for padding_px seed policy, edge-pixel bleed fill, inner-content UVs, ninety-degree clockwise rotation shelves, multi-frame glyphs, scalable seed multipliers, and oversized abort before writing outputs.

atlaspack probe accepts --atlas, --manifest, --glyph, --frame, --u, and --v. It must sample atlas pixels at normalized UV coordinates for a glyph frame per the same contracts and exit per /app/docs/exit-codes.md.

Bundled catalogs and sprites live under /app/fixtures/. Do not edit /app/docs/, /app/fixtures/, or /tests/.
