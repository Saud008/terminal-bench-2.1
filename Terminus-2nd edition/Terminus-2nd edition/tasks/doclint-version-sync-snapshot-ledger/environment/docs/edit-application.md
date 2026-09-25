# Edit application

When multiple `contentChanges` arrive in one `didChange`, normalize them into staged edits and append to the staging queue per `/app/docs/staging-flush.md`. Staging **accumulates raw per-batch edits across batches** -- it does not collapse each batch into a single full-buffer replacement before the next change arrives.

To compute the **working text** (committed text plus all pending staging), sort the full staging list by `(start.line, start.character)` **descending**, then apply edits **one at a time** to an evolving buffer. After each edit, recompute UTF-16 byte offsets from the **current** buffer contents, not from the original pre-change snapshot. For non-overlapping edits this matches pre-computing all offsets from the base; overlapping ranges (e.g. beta22/gamma99 ascii-overlap fixtures) require the descending evolving-buffer order.

Full-buffer replacements use a missing `range` field. When converting a batch to edits, resolve a missing `range` against the **current working text** at acceptance time; append the resulting edits to staging without merging prior queued edits.

At flush (close or export), apply the accumulated staging list to committed text with the same descending evolving-buffer algorithm, then clear staging.

Application uses UTF-16 offsets per `/app/docs/utf16-positioning.md`.
