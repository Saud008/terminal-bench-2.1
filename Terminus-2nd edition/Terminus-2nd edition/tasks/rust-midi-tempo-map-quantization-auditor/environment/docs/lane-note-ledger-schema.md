# Note ledger schema

Files live at /app/work/lane-note-ledger/<run-id>.jsonl. The first line is a header with run_id and chart_id. Each following line is a note stage row with id, lane, raw_tick, quantized_tick, and rejected_overlap boolean sorted by id ascending.
