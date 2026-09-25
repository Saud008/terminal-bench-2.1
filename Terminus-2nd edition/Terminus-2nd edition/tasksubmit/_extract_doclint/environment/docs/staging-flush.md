# Tamper-evident staging flush

The document model splits **committed text** and a **tamper-evident staging queue** of pending edits. Each `didChange` appends that batch's normalized edits to staging with `extend`-style accumulation -- raw staged edits from every batch remain in the queue until a flush authenticity gate; batches are not collapsed into one replacement edit.

| Event | Required authenticity behavior |
|-------|--------------------------------|
| `didChange` | Append normalized edits to staging; update version only after merge rules in the admission contract |
| `didClose` | Flush staging into committed text, then clear staging |
| `doclint.exportSnapshot` | Flush staging before reading text or computing diagnostics |

Export and close paths share the same flush primitive. Partial fixes that flush on close but not on export (or vice versa) fail downstream attestation checks.
