# Shingle window

Mail bodies are extracted from each .eml file by taking all lines after the first blank line (headers/body separator). Normalize the body by lowercasing and collapsing runs of whitespace to a single ASCII space, then strip leading and trailing space.

For normalized body text of length L and window size W:

- If L < W, the mail contributes zero shingles.
- Otherwise emit one shingle per start offset i in the inclusive range 0 through L - W (zero-based). Each shingle is the contiguous substring of length exactly W starting at i.

Hash each shingle as lowercase hex of the first 16 bytes of SHA-256 over the UTF-8 string key_epoch:checksum_algo_id:shingle where key_epoch and checksum_algo_id come from the active key manifest.

The awk shingle emitter must receive the same window-size integer the CLI passes; do not adjust it internally.
