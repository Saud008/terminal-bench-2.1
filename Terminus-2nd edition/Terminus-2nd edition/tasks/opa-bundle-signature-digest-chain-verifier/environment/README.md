# bundlectl

Local tool for verifying OPA-style signed policy bundles and evaluating a constrained Rego subset.

- Contract acceptance: `/app/docs/import-preview-contract.md`
- Bundle protocol: `/app/docs/bundle-contract.md`
- Eval trace schema: `/app/docs/eval-trace-schema.md`
- Fixtures: `/app/docs/fixture-catalog.md`

Rebuild:

```bash
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
go build -mod=readonly -o /usr/local/bin/bundlectl ./cmd/bundlectl
```
