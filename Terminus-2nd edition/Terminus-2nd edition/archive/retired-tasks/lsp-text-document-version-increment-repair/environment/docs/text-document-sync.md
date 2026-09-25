# Text document sync

`term-lsp` keeps one in-memory document per URI. `textDocument/didOpen` seeds committed text and sets document version to the client-supplied `textDocument.version` (use **0** only when the client omits a version). Each `textDocument/didChange` carries the client’s monotonic `textDocument.version` and a list of incremental `contentChanges`.

Changes are appended to **staging** first. Committed `text` updates only after an explicit **flush** (`textDocument/didClose` or export). The server must expose the post-flush version only after staging merges into committed text — never before edits are applied.

`textDocument/didClose` must flush staging into committed text before clearing the staging queue. Closing with pending staging must not discard edits.

Replay of the same `(uri, version)` change batch must be ignored after the first successful application.

After `doclint.exportSnapshot` returns flushed text and version, a new server process may `textDocument/didOpen` the same URI with that text and version; a subsequent export must round-trip the same values without re-applying prior change batches.
