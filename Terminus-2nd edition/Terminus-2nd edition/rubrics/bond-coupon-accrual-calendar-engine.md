# Platform rubric — bond-coupon-accrual-calendar-engine

**Task folder:** tasks/bond-coupon-accrual-calendar-engine/

Agent seeds bond schedules and coupon ladders into /app/state/accrual.db, +3
Agent applies business-day settlement lag skipping weekends and holidays, +3
Agent computes ACT/360 year fractions with 360 denominator not calendar year, +3
Agent aligns semi-annual coupon dates with end-of-month issue anchors, +3
Agent zeroes accrued interest when trade date is on or after ex-coupon date, +3
Agent accrues from issue through settlement date not trade date alone, +3
Agent advances accrual_pass gate to at least two before atlas publish, +3
Agent publishes accrual-atlas.json with rows sorted by trade_id, +3
Agent computes atlas_digest as sha256 over canonical row JSON payload, +3
Agent rebuilds bondacc via verifier-rebuild.sh before subprocess CLI checks, +2
Agent honors TB3_EX_DAYS override on hidden ex-days-trap scenarios, +2
Agent uses calendar-day settlement lag ignoring holiday calendar, -3
Agent divides ACT/360 accrual by 365 day count denominator, -3
Agent skips Modified Following roll when forward adjustment crosses month, -3
Agent treats ex-coupon boundary with strict after instead of inclusive compare, -3
Agent publishes atlas when accrual_pass is still one after trades only, -3
Agent hashes atlas_digest from scenario slug string without row payload, -3
