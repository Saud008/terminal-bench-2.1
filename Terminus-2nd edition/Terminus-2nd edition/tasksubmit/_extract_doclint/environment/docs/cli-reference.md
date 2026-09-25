# Admission surface reference

Binary: `/usr/local/bin/term-lsp` (stdio framed admission transport).

Supported admission verbs: `initialize`, `initialized`, `textDocument/didOpen`, `textDocument/didChange`, `textDocument/didClose`, `workspace/executeCommand` (`doclint.exportSnapshot`), `shutdown`, `exit`.

Refresh the binary after authenticity-policy edits: `cargo build --release --locked -p term-lsp`.

Reset attested state: `bash /app/scripts/reset-state.sh`.
