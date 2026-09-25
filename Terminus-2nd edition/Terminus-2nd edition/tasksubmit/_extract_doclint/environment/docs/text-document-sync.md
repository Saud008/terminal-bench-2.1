# Version-admission integrity path

`term-lsp` keeps one in-memory attested document per URI. `textDocument/didOpen` seeds committed text and sets document version to the client-supplied `textDocument.version` (use **0** only when the client omits a version). Each `textDocument/didChange` carries the client's monotonic `textDocument.version` and a list of incremental `contentChanges`.

Changes are appended to **tamper-evident staging** first. Committed `text` updates only after an explicit **flush authenticity gate** (`textDocument/didClose` or export). The plane must expose the post-flush version only after staging merges into committed text -- never before edits are applied.

`textDocument/didClose` must flush staging into committed text before clearing the staging queue. Closing with pending staging must not discard admitted edits.

Replay of the same `(uri, version)` change batch must be ignored after the first successful application (anti-replay).

After `doclint.exportSnapshot` returns flushed text and version, a new process may `textDocument/didOpen` the same URI with that text and version; a subsequent export must round-trip the same attested values without re-applying prior change batches.
