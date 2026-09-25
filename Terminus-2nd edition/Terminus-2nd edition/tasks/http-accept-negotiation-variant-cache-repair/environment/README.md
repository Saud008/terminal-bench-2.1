# variantgate

HTTP resource server with Accept-family negotiation and a Vary-aware response cache.

```bash
go build -mod=readonly -o /usr/local/bin/variantgate ./cmd/variantgate
variantgate serve --listen 127.0.0.1:8080 --catalog /app/fixtures/catalog.json
```

Contracts: `/app/docs/negotiation-contract.md`, `/app/docs/negotiation-snapshot.md`, `/app/docs/publish-contract.md`, `/app/docs/cache-contract.md`
