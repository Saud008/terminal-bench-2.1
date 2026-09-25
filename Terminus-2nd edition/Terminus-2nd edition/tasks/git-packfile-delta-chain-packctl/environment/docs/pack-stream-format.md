# Pack stream layout

Each object in pack.stream is stored contiguously:

| Field | Width | Meaning |
|-------|-------|---------|
| kind | 1 byte | 1=blob, 2=tree, 4=commit, 6=ofs_delta, 7=ref_delta |
| compressed_size | u32 big-endian | length of following zlib blob |
| data | compressed_size bytes | zlib payload |

Blob and tree payloads zlib-compress raw inflated bytes. Delta kinds zlib-compress UTF-8 patch scripts defined in pack-delta-patch.md.

The catalog.json pack_offset for each entry is the byte offset of that object kind byte in pack.stream. Entries appear in catalog order; offsets are monotonic.

Ingest copies catalog metadata into /app/state/pack-stage.json without inflating objects. Resolve reads pack.stream through staging paths only.
