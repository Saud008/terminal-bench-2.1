# Platform rubric — miniz-deflate-block-boundary-checksum-decoder

**Task folder:** tasks/miniz-deflate-block-boundary-checksum-decoder/

Agent inflates public zlib fixtures to byte-identical reference output, +3
Agent writes staging snapshot with per-block metadata before report finalization, +3
Agent computes staging_adler matching independent Adler-32 over all emitted bytes, +3
Agent continues decode past zero-length non-final stored blocks in chained streams, +3
Agent decodes dynamic Huffman blocks with correct code-length table rebuild order, +3
Agent applies sliding-window LZ77 copies that span DEFLATE block boundaries, +3
Agent records stored block_checksum as low 16 bits of payload byte sum only, +2
Agent sets Huffman block block_checksum field to zero in staging JSON, +2
Agent exits with status 2 on zlib trailer Adler mismatch after decode, +2
Agent produces byte-identical output and report on repeated decompress runs, +2
Agent rebuilds minizdecode with cargo after Rust module edits, +2
Agent patches only Adler while leaving broken empty-block handling in stream.rs, -3
Agent fixes Huffman decode but emits wrong staging block indexes or final flags, -3
Agent skips empty middle stored block so chained fixtures truncate payload, -3
Agent records stored checksum over block header bytes not payload only, -2
Agent treats zlib checksum mismatch as exit 1 instead of contract exit 2, -2
