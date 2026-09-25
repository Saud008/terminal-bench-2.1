# CLI reference

Binary: `/usr/local/bin/term-lsp` (stdio JSON-RPC, Content-Length framing).

Supported methods: `initialize`, `initialized`, `textDocument/didOpen`, `textDocument/didChange`, `textDocument/didClose`, `workspace/executeCommand` (`doclint.exportSnapshot`), `shutdown`, `exit`.

Rebuild: `cargo build --release --locked -p term-lsp`.

Reset state: `bash /app/scripts/reset-state.sh`.
