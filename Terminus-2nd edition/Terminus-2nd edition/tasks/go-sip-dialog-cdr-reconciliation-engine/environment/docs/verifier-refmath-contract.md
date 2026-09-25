# Verifier reference math

Pytest helpers sip_cdr_refmath.py and sip_transcript_runner.py use Python sqlite3 and hashlib only. They recompute to-tag fork compile using (ts_ms,cseq) sort, branch keys, provisional gating, CANCEL precedence, retransmission collapse, skew, inclusive billing windows, and SQLite row filter independent of Go sources.
