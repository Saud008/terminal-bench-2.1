# SQLite inspection contract

inspection.db is a SQLite database written by modernc.org/sqlite in wfhistctl. Table activity_inspection columns: run_generation, activity_id, attempt, status, risk_score. Rows insert in sort order run_generation, activity_id, attempt ascending. Operators may inspect rows with the sqlite3 CLI.
