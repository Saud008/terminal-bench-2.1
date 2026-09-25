# Submission explanations — bond-coupon-accrual-calendar-engine

**Task folder:** tasks/bond-coupon-accrual-calendar-engine/
**Platform form only** — not in upload zip.
**Updated:** 2026-07-09T18:11:07Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

Agents must wire bondacc so coupon schedules, holiday calendars, day-count conventions, settlement lag, ex-coupon windows, and SQLite accrual rows all agree. The hard part is financial date math across modules: ACT/360 uses a 360 denominator, settlement skips weekends and holidays, EOM bonds need month-end coupon alignment, and ex-coupon cuts accrued interest on the correct calendar day. Contracts live in nine /app/docs files, not the short instruction. Fixing one file often passes some scenarios while atlas digest, pass-gate, or hidden TB3 fixtures still fail. Partial fixes on trade date vs settlement date or digest over scenario-only bytes are common traps.

## Solution Explanation

The oracle applies a unified patch to eight Go modules under /app/internal, rebuilds bondacc, and runs the same CLI pipeline agents use. The main insight is accrual must use settlement date after business-day lag, period bounds from the coupon ladder anchored at issue, and atlas_digest from sorted row JSON not the scenario name. Calendar adjustment, day-count fractions, ex-coupon inclusivity, pass gate threshold, and publish gating must align before publish-atlas succeeds.

## Verification Explanation

test.sh rebuilds bondacc before pytest. Twenty-two tests invoke /app/bin/bondacc via subprocess and compare outputs to independent reference math in bond_refmath.py, including sqlite3 reads of accrual.db and hashlib recomputation of atlas_digest. Hidden traps under TB3 fixture dirs use different ex-coupon and calendar cases than bundled scenarios. NOP on the broken baseline should score zero. Oracle patch plus rebuild should pass all tests.
