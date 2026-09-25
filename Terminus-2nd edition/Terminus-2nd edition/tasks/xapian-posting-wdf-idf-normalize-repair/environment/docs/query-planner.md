# Query planner

Query strings are lowercase terms separated by AND or OR. AND requires every term present with positive effective_wdf to contribute. OR includes every term whose effective_wdf is positive.

A term is rare when cf(t) <= TB3_RARE_CF (default 2). Rare terms still multiply by the full idf(t) on OR branches; skipping IDF is not permitted for any collection frequency.
