# SQLite refresh persistence

Database path: /app/state/formulary.db

Table matrix_rows primary key (plan_id, ndc_normalized).

refresh-db must UPSERT rows so a second refresh without roster mutation replaces rows without increasing row count.

refresh_revision increments by one on each successful refresh-db.
