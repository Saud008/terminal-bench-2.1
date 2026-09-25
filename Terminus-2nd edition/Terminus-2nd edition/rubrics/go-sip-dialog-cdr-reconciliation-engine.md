# Platform rubric — go-sip-dialog-cdr-reconciliation-engine

**Task folder:** tasks/go-sip-dialog-cdr-reconciliation-engine/
**Form category:** Game (zip `games`; bash/python playtest desk)

Agent ingests SIP transcript JSONL with ts_ms and cseq ordering, +3
Agent joins dialog branches on Call-ID plus To-tag per branch contract, +3
Agent treats 183 Session Progress as non-answer for CDR export, +3
Agent applies CANCEL precedence over BYE when both appear pre-answer, +3
Agent suppresses duplicate SIP retransmits before dialog compile, +3
Agent shifts answer timestamps by clock_skew_ms before billing, +3
Agent rates calls with inclusive billing window end minute, +2
Agent exports only answered dialogs with final disposition to SQLite, +3
Agent writes dialog-buffer.json with dialog_seal before export-cdr, +2
Agent reads TB3_FIXTURE_DIR for hidden cancel poison scenarios, +2
Agent produces byte-stable cdr.sqlite on cross-run idempotent replay, +2
Agent keeps /app/bin/sipcdrctl current after /app/lib/sipcdr edits, +1
Agent leaves decoy module off export hot path, +1
Agent sorts cdr_rows by call_id then branch_key ascending, +2
Agent sorts transcript by cseq only ignoring ts_ms tie order, -3
Agent exports provisional-only legs into cdr.sqlite, -3
Agent prefers BYE over CANCEL when both terminate same branch, -3
Agent drops retransmit duplicates causing duplicate SQLite rows, -3
Agent ignores clock_skew_ms when rating peak versus offpeak, -3
Agent uses non-canonical Dockerfile base image, -5
