# Metadata precedence

Layer archives are applied in ascending layer index order.

When the same normalized path appears in multiple layers, the entry from the highest layer index wins for presence, uid, gid, and mode.

Whiteout and opaque markers use the layer index of their tar member when determining which lower entries they affect.

Directories and files are independent paths. A file entry does not imply its parent directory unless a directory member exists or is implied by the materializer.
