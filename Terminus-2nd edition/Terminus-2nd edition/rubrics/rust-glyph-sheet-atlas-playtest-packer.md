# Platform rubric — rust-glyph-sheet-atlas-playtest-packer

**Task folder:** tasks/rust-glyph-sheet-atlas-playtest-packer/
**Written:** 2026-07-19T17:45:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent aligns catalog, pack, UV, manifest, and atlas modules so pack and probe match the playtest contracts, +3
Agent applies padding_px seed policy and replicates edge-pixel bleed into the gutter, not transparent fill, +3
Agent emits inner-content UV rectangles that exclude the padded gutter for bilinear edge samples, +3
Agent places rotated sprites with swapped shelf size and ninety-degree clockwise compositing, +2
Agent keeps multi-frame glyphs and scalable seed multipliers consistent across pack sets, +2
Agent aborts oversized scaled sprites with exit code 2 before writing atlas outputs, +2
Agent rebuilds the release atlaspack binary before verifier runs, +1
Agent leaves /app/docs, /app/fixtures, and /tests unchanged, +1
Agent fixes only UV math while padding bleed or rotation shelves stay wrong, -3
Agent fills gutter with transparent pixels instead of edge replication, -3
Agent edits protected fixtures or the verifier reference under /tests to force a pass, -5
