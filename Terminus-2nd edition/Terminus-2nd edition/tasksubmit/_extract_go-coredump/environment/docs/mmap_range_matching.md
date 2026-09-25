# mmap integrity range gates

Program counter authenticity resolution uses **half-open** integrity intervals `[start, end)` on virtual addresses.

Parse hex start/end from mmap entries. A PC is admitted when `start <= pc < end`.

When multiple mappings match, prefer the entry with the **largest** `file_offset` (tie-break toward later mapping).

Compute the file-relative authenticity offset as **virtual PC minus mmap start plus file_offset** (all parsed as unsigned hex).
