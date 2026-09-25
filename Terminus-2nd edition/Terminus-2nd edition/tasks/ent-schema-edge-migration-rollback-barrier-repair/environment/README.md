# entmigrate

Offline ent-style schema edge migration tool for SQLite. See /app/docs/migration-pipeline.md for the up/down contract.

Commands:

- entmigrate up --catalog PATH --db PATH --seed NAME --report PATH
- entmigrate down --catalog PATH --db PATH --steps N --report PATH
