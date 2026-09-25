# Word order and signed int32

Two 16-bit words form a signed int32 engineering raw value.

## Default order

big_endian_words: high word first. raw = (words[0] << 16) | (words[1] & 0xFFFF).

## Override

Manifest default_word_order or per-register override word_order little_endian_words swaps order: raw = (words[1] << 16) | (words[0] & 0xFFFF).

## Signed interpretation

When width is int32, interpret raw as two's complement 32-bit signed integer.

## uint16

Single word registers use words[0] only as unsigned 16-bit raw.

Scale factors apply to the decoded raw integer the same way for both widths.
