# Verifier reference math

Pytest helpers duel_ledger_refmath.py and duel_admit_runner.py use Python sqlite3 and hashlib only. They recompute fork_tag lane fold using (ts_ms,cseq) sort, branch keys, hold gating, FORFEIT precedence, retransmission collapse, skew, inclusive score windows, and SQLite row filter independent of the shipped policy modules.
