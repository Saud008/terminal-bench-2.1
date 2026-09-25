# ELF GNU build-ID authenticity notes

Build IDs are authenticity digests read from PT_NOTE segments in companion ELF binaries referenced by mmap paths.

For each ELF file, scan note sections. GNU build-ID note type is `0x3`. The descriptor bytes form the authenticity build ID used for trust admission.

Canonical attestation form: **uppercase hex** without `0x` prefix (for example `AB12CD34...`).

Note header fields `namesz` and `descsz` in each note record use **little-endian uint32** layout on the target platform.
