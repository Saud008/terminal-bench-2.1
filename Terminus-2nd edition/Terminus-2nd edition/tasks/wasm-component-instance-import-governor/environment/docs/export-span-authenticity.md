# Export section span authenticity

Integrity gate for export admission: the export section begins with an unsigned LEB128 length prefix followed by exactly that many payload bytes.

Admission must confirm the length does not exceed remaining bytes before reading export kind discriminants inside the payload. Reading kind tags before validating the span is incorrect.

Kinds are single-byte values where 1 means function export and 2 means nested instance export.

A package whose declared span exceeds the bytes remaining in the file is inadmissible. Admission of such a package aborts the whole load pass: `component-gov load` exits nonzero, reports the failure on stderr with a message naming the export section, and leaves `/app/state/import-alias.bin` unwritten.
