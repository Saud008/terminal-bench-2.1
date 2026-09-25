# CLI / method reference

Binary: `/usr/local/bin/term-lsp` (stdio JSON-RPC transport).

Supported methods: `initialize`, `initialized`, `textDocument/didOpen`, `textDocument/didChange`, `textDocument/didClose`, `workspace/executeCommand` (`doclint.exportSnapshot`), `shutdown`, `exit`.

Refresh the binary after crate edits: `cargo build --release --locked -p term-lsp`.

Reset in-memory document state: `bash /app/scripts/reset-state.sh`.
