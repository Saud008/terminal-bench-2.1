# Skip-gap preservation

Skip-gap spans are GAPS-marked byte ranges recorded in the staging ledger during ingest.

Relayout export must emit a wire buffer that still contains every ledger gap span at the same start offset and length as the source wire captured during ingest.

Compacting away gap filler bytes before export is incorrect even when table bodies are relocated.

The bundled scene_a wire contains one skip-gap span at offset zero. Exported relayout.wire must still contain the GAPS magic at offset zero.
