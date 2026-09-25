# Text document sync path

`term-lsp` keeps one in-memory document per URI. `textDocument/didOpen` seeds committed text and sets document version to the client-supplied `textDocument.version` (use **0** only when the client omits a version). Each `textDocument/didChange` carries the client's `textDocument.version` and a list of incremental `contentChanges`.

Changes are appended to a **staging queue** first. Committed `text` updates only after an explicit flush (`textDocument/didClose` or export). The exported version must reflect the post-flush document -- never a value bumped before staging merges.

`textDocument/didClose` must flush staging into committed text before clearing the staging queue. Closing with pending staging must not discard accepted edits.

A change whose `(uri, version)` was already applied successfully must be ignored (no re-append, no re-apply).

After `doclint.exportSnapshot` returns flushed text and version, a new process may `textDocument/didOpen` the same URI with that text and version; a subsequent export must round-trip the same values without re-applying prior change batches.
