# Fixture catalog

Bundles live under `/app/fixtures/bundles/`. Seeds are in `/app/fixtures/seeds.json`.

## Good bundles (verify + eval must succeed)

| Bundle | Notes |
|--------|-------|
| `allow-basic` | Single policy, `data.foo` drives allow |
| `deny-edge` | Default deny unless input high |
| `multi-scope` | Two signature scopes (`policies/`, `data/`); `data/` has multiple members in manifest order (not lexicographic) |
| `path-normalize` | Manifest lists `./data/../data/data.json` alias; must canonicalize to `data/data.json` |

Run `bundlectl verify --bundle <dir>` once per good bundle (no `--seed`). Run `bundlectl eval` with every seed in `seeds.json`.

## Trap bundles (verify must fail)

| Bundle | Expected failure |
|--------|------------------|
| `tampered-member` | `data/data.json` bytes altered, signatures unchanged |
| `revoked-signer` | Signed with revoked `key_id` |
| `bad-scope-chain` | Scoped `chain_root` does not match subset digest |
| `path-escape` | Manifest member `../../etc/passwd` must be rejected during import-preview |

## Queries

Eval always targets package `policy`, rule `allow`. Inputs are in each bundle's `input/default.json`.
