# Tempo ledger schema

Files live at /app/work/tempo-ledger/<run-id>.jsonl. The first line is a JSON header with run_id and row_type header. Each following line is a tempo event with tick and microseconds_per_quarter sorted by tick ascending.
