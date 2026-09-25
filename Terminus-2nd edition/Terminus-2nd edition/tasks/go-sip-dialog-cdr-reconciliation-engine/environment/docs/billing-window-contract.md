# Billing windows

policy.json defines windows array with name, start_minute, end_minute inclusive within UTC day, and tier label.

rate-billing assigns billing_tier using adjusted answer_ts minute-of-day. End minute is inclusive.

The default peak window uses tier label peak for minutes 480 through 1020 inclusive. Offpeak covers minutes 0 through 479 inclusive.
