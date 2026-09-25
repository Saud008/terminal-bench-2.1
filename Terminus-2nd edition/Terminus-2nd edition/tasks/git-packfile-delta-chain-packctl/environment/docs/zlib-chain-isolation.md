# Zlib chain isolation

Each pack object inflate, including every hop in a multi-link delta chain, must decode zlib into a dedicated output buffer.

Reusing one scratch buffer across links without zeroing lets later patches read stale trailing bytes from earlier objects. Chain isolation requires a fresh Vec per inflate_at call.
