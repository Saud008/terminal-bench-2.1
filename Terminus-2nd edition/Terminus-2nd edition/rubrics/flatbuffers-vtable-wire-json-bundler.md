# Platform rubric — flatbuffers-vtable-wire-json-bundler

**Task folder:** tasks/flatbuffers-vtable-wire-json-bundler/
**Written:** 2026-07-28T04:15:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent resolves vtable soffset by subtracting from table position, +3
Agent maps vtable field offsets as absolute table plus field_off, +3
Agent follows uoffsets by adding field_pos plus offset, +3
Agent preserves tag vector wire order without reverse iteration, +3
Agent omits absent tags rather than synthesizing empty arrays, +2
Agent reads Vec3 fields in x y z little-endian order without swap, +2
Agent writes staging envelope with sixteen-hex hn55 digest field, +3
Agent appends ledger lines with matching hn55 and export_digest digests, +3
Agent exports JSON through stdout_render without sorting tag keys, +2
Agent rejects export when ledger export_digest no longer matches staging, +2
Agent reports verify aligned true or false with exit 0 or 1, +2
Agent exits 2 when required schema or input flags are missing, +1
Agent adds soffset to table position for vtable anchor, -3
Agent uses wrapping_sub for field absolute addresses, -3
Agent reverses tag vector elements on read, -3
Agent coerces missing tags to empty arrays in staging snapshot, -2
Agent serializes wire digest under wire_digest instead of hn55, -3
Agent sorts tags by key before stdout JSON export, -2
Agent skips ledger alignment checks on export, -2
Agent edits docs schema or fixtures instead of Rust sources, -1
