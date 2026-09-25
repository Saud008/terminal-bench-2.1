# oidguard

Machine-bound BSON wire-id admission attestation governor with witness-sealed vault commits and path-scoped reapplication.

```bash
go build -mod=readonly -o /usr/local/bin/wireclock ./cmd/wireclock
oidguard serve --listen 127.0.0.1:9090 --db /app/data/oidguard.db
```

See `/app/contracts/wireclock-governor.md` and the linked wire-id, witness, reapply, and CLI contracts.
