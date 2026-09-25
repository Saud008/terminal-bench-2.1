# Token normalization contract

Every document body passes through Unicode normalization, case folding, punctuation stripping, and whitespace tokenization before shingle generation.

Apply NFKC normalization to the raw body string, then lowercase the result. Split on ASCII whitespace into tokens. Strip leading and trailing characters from the set period comma exclamation question semicolon colon apostrophe double-quote parentheses square brackets and curly braces from each token. Drop empty tokens after stripping.

The normalized token sequence feeds shingle generation. Do not apply NFC-only normalization.
