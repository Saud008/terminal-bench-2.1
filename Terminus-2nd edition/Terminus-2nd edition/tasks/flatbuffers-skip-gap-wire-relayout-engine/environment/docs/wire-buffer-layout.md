# Wire buffer layout

Game-asset FlatBuffers wire images in this task use a simplified wire layout compatible with standard little-endian scalar rules.

## Single-root footer

When the last twelve bytes are not an MR2R multi-root footer, the final four bytes store root_uoffset as u32 little-endian. The root table starts at buffer_length minus four minus root_uoffset.

## Multi-root footer

When bytes at length minus twelve through length minus eight equal the ASCII sequence MR2R, the footer is twelve bytes:

- bytes length minus eight through length minus four: secondary_root_uoffset u32 little-endian
- bytes length minus four through length: primary_root_uoffset u32 little-endian

Each offset is measured backward from the byte immediately before the twelve-byte footer.

## Table and vtable

Each root table begins with vtable_soffset as i32 little-endian. The vtable lives at table_start plus vtable_soffset.

The vtable header is vtable_len int16 little-endian then object_size int16 little-endian, followed by voffset_t slots as int16 little-endian values.

## Skip-gap regions

A skip-gap region begins with the four-byte magic GAPS, followed by u32 little-endian payload length, followed by payload bytes. Relayout export must preserve every skip-gap byte span listed in the staging ledger.
