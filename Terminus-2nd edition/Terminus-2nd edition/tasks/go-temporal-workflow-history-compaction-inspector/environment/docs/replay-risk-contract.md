# Replay risk ledger contract

replay-risk-report.jsonl emits one JSON object per line per run_generation with workflow_id, run_generation, risk_code, pending_timers, max_attempt. risk_code is RETRY_CHAIN when max_attempt exceeds one, TIMER_PENDING when pending_timers positive, otherwise CLEAN.
