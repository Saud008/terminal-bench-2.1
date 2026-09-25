# Quality mask gate

Exclude a star from binding and from the sealed active set when
`(det_mask | cat_mask) & 0x04 != 0`. Bit `0x04` is the laboratory reject bit.
