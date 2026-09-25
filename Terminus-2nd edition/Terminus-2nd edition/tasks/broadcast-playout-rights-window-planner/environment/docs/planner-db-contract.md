# Plan store contract

compile-windows persists rows in syndication-plan.db table plan_rows. Pytest uses the sqlite3 standard library module to count rows after repeated compile passes. Repeated compile-windows for the same scenario replaces prior rows for that scenario without increasing row count.

run_stamp is first 16 hex chars of sha256(runway_digest + pipe + scenario name).
