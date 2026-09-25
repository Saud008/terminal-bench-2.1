# Platform rubric — flatbuffers-skip-gap-wire-relayout-engine

**Task folder:** tasks/flatbuffers-skip-gap-wire-relayout-engine/

Agent decodes vtable header and slot offsets as little-endian u16 values, +3
Agent applies table alignment padding only after rewriting the vtable soffset, +3
Agent copies GAPS-marked skip-gap spans verbatim into relayout.wire, +3
Agent validates vtable byte length before reading field presence slots in ingest, +2
Agent computes wire-seal.txt only after gap restoration completes, +3
Agent reads /app/state/vtable-ledger.bin during relayout export without re-reading ingest wires, +2
Agent rebuilds fbctl with cargo in test.sh after editing vtable or relayout modules, +2
Agent records both MR2R footer roots in the staging ledger for gamma wire fixtures, +2
Agent leaves src/decoy off the ingest and relayout export hot path, +1
Agent uses big-endian or native-endian reads for vtable slot scalars, -3
Agent inserts alignment padding before vtable pointer fixup corrupting the root footer, -3
Agent compacts away skip-gap filler bytes during relayout export, -3
Agent hashes relayout.wire before gap spans are restored into the output buffer, -3
Agent checks field presence bits on a truncated vtable during ledger write, -2
