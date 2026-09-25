# UTF-16 positioning

LSP ranges use 0-based lines and **UTF-16 code unit** offsets within each line (BMP code points count as 1; supplementary characters such as emoji count as 2).

Byte offsets in the Rust UTF-8 buffer must be derived by walking each line’s characters and accumulating `char.len_utf16()`. Do not treat `character` as a UTF-8 byte index or Rust scalar index.

Surrogate-pair fixtures under `/app/fixtures/sources/` exercise wide characters; incorrect conversion shifts every subsequent edit in a batch.
