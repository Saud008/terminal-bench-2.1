# Redis stream key naming

Stream keys in bundled journals use short names like orders, events, jobs, and ledger. Hidden verifier journals may prepend TB3_STREAM_PREFIX to every stream field before replay.

The replay engine must preserve group and pending state under the prefixed stream key without collapsing groups across prefixes.
