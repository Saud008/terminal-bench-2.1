# Strike settlement contract

For each non-curtailed reading:

1. Look up market price in price_cents for the aligned interval_start_utc (exact string match on interval_start_utc in market_prices).
2. settlement_cents = max(strike_price_cents, market price_cents)
3. amount_cents = round half up of mwh times settlement_cents (mwh is floating megawatt-hours)

Settlement lines include strike_cents, market_cents, settlement_cents, and amount_cents fields.

When market price exceeds strike price, settlement uses the market price. When strike exceeds market, settlement uses strike.

Missing market price for an aligned interval is an error during compile-lines.
