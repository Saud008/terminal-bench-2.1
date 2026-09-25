# Fixture catalog

Sample registries live under `/app/fixtures/registry/`. Each directory contains one `registry.yml`.

| Directory | Scenario focus |
|-----------|----------------|
| `001-transitive-runner` | transitive runner inheritance |
| `002-symlink-prefix` | prefix symlink canonicalization |
| `003-dxvk-semver` | DXVK semver pin enforcement |
| `004-duplicate-merge` | duplicate slug merge with warning |
| `005-missing-runner` | missing inherited runner |
| `006-deep-chain` | deep `requires:` closure depth |
| `007-requires-cycle` | directed cycle detection |
| `008-missing-slug` | absent required slug |
| `009-conflicting-duplicate` | conflicting duplicate merge |
