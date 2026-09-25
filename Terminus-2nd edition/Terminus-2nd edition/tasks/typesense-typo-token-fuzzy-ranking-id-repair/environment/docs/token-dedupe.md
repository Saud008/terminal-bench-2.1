# Token dedupe for indexing

When indexing a document, dedupe tokens by NFC-normalized form while preserving distinct NFC codepoint sequences. Do not apply NFKC compatibility decomposition: distinct compatibility characters such as circled letters must remain separate index terms even when ASCII lookalikes exist.

Lowercase split tokens on whitespace before dedupe. Use NFC normalization only to build the dedupe key that decides whether two tokens are duplicates. The token string stored in the inverted index and returned in index term lists is the original lowercase token from the document text (first occurrence wins when two tokens share an NFC key). Do not replace stored tokens with their NFC-normalized form when inserting index entries.

Each surviving token is inserted into the inverted index once per document.
