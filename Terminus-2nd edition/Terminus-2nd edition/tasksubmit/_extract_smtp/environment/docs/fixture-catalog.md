# Fixture catalog

| Path | Purpose |
|------|---------|
| `/app/fixtures/mail/` | Mixed `.eml` and `.mbox` mail fragments for the default index command |
| `/app/data/thread.db` | Empty SQLite thread database initialized at image build |
| `/app/data/schema.sql` | Database schema applied at image build |
| `/app/docs/thread-index-schema.md` | Parsed-message field types, thread union rules, report and SQLite contract |

Hidden verifier mail may appear only under `/opt/verifier-fixtures/` when `TB3_SMTP_FIXTURES` is set to that directory.

Default invocation:

```text
mailindex index --mail-dir /app/fixtures/mail --thread-db /app/data/thread.db --output /app/output/thread-index.json
```
