# Relayout padding

When relocating root tables, alignment padding may be required so that vtable pointers remain valid.

Padding bytes must be applied only after the vtable soffset at the table head is rewritten to point at the relocated vtable.

Inserting alignment padding before rewriting the vtable soffset shifts table positions while the root footer still references the pre-padding offset, which corrupts the exported wire image.

Relayout export for bundled scene_a must produce a buffer with the same length as the ingested scene_a wire when no table bodies move.
