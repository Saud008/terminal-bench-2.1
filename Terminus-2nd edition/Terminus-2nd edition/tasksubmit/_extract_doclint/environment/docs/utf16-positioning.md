# Position integrity (UTF-16)

Admission ranges use 0-based lines and **UTF-16 code unit** offsets within each line (BMP code points count as 1; supplementary characters such as emoji count as 2). This is a position-integrity gate: misaligned offsets shift every subsequent edit and break attestation round-trips.

Byte offsets in the UTF-8 buffer must be derived by walking each line's characters and accumulating `char.len_utf16()`. Do not treat `character` as a UTF-8 byte index or scalar index.

Surrogate-pair fixtures under `/app/fixtures/sources/` exercise wide characters; incorrect conversion fails position-integrity checks on later edits in a batch.
