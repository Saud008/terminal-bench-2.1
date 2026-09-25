The variantgate HTTP service under /app serves negotiated resource variants from /app/fixtures/catalog.json with a Vary-aware response cache. Negotiation stages a snapshot at /app/state/negotiation.snapshot.json and selects catalog variants from prepared Accept-family headers. The response cache keys on raw request header strings.

All behavioral requirements are normatively defined in /app/docs/negotiation-contract.md, /app/docs/negotiation-snapshot.md, /app/docs/publish-contract.md, /app/docs/cache-contract.md, and /app/docs/snapshot-guard-contract.md. Repair the Go packages under /app/internal/ so bundled fixtures and catalogs loaded through POST /admin/catalog behave per those contracts. The environment has no outbound network access.

Preserve existing exported function and type names in /app/internal/negotiate/ and /app/internal/staging/ (for example ParseList, RankEntries, BetterCandidate, Digest). Implement missing or broken behavior only. Do not rename symbols consumed by other packages.

After repair, `/usr/local/bin/variantgate` must build from `/app` with `go build -mod=readonly` and must serve negotiated responses for catalogs under `/app/fixtures/` (including admin catalog reload) while honoring the contracts above.

Do not edit `/app/docs/` or `/app/fixtures/`.
