# Score windows

policy.json defines windows array with name, start_minute, end_minute inclusive within UTC day, and tier label.

score-windows assigns score_band using adjusted answer_ts minute-of-day. End minute is inclusive.

The default rush window uses tier label rush for minutes 480 through 1020 inclusive. Calm covers minutes 0 through 479 inclusive.
