# Fixture catalog

Bundled route dumps under `/app/fixtures/dumps/`:

- `001-multipath-v4.bin`
- `002-nh-id-scope.bin`
- `003-v6-gateway.bin`
- `004-table-override.bin`
- `005-metrics-nested.bin` — `RTA_METRICS` count-prefixed nested entries (`mtu`, `advmss`)
- `006-mixed-dual.bin`
- `007-alt-seed.bin`
- `008-v6-multipath.bin`
- `009-table-multipath.bin` — `RTA_TABLE` override with multipath hops
- `010-three-hop-priority.bin` — three-hop multipath with `RTA_PRIORITY`, `RTA_TABLE` override, and non-monotonic scaled weights
- `011-v6-dst-minimal.bin` — IPv6 destination with interior zero groups requiring minimal hex formatting
- `012-route-message-order.bin` — two routes with descending table ids to verify dump message order is preserved
- `013-dual-multipath-nh-chain.bin` — two multipath routes with seed `nl-seed-13` to exercise bind→NH snapshot staging
- `014-multipath-metrics-isolated.bin` — multipath route with route-level `RTA_METRICS` that must not attach to nexthop rows

`nlctl decode` must succeed for every file above.

## Combined decode scenarios

nlctl decode must also succeed for synthetically built NLDM dumps that are not checked into /app/fixtures/dumps/. These scenarios stress cross-stage invariants within a single invocation:

| Header seed | Scenario |
|-------------|----------|
| nl-proc-seed-7 | IPv4 multipath with RTA_TABLE override and seed-scaled hop weights |
| nl-proc-chain-3 | Two-route chain: IPv6 minimal dst with multipath gateways, then IPv4 route with RTA_TABLE override, nested RTA_METRICS on a multipath route, and three-hop multipath |
| TB3-nl-cross-stage-9 | Two-route chain mixing single-path metrics attachment and multipath table override in one dump |
| TB3-nl-guard-metrics-4 | Single-path route with route-level RTA_METRICS that must pass stage 1b guard |

A correct implementation aligns bind snapshots, NH snapshots, export JSON, and export_digest for every catalog file and every combined scenario above. Decoding all catalog dumps alone is not sufficient when cross-stage staging or digest rules remain broken.

Hidden and procedural dumps may be built at verify time using header seeds above. When present, VERIFIER_SEED overrides the default procedural seed (nl-proc-seed-7 / PROC_SEED). CHAIN_SEED, TB3_SEED, and TB3_METRICS_SEED name the combined-scenario seeds in the table; TB3_METRICS_SEED and TB3_SEED identify the guard-metrics and cross-stage overlays.

Verifier cross-run probes write paired reports such as cross-run-a.json, cross-run-b.json, digest-a.json, digest-b.json, digest-ref.json, and digest-source.json under /app/output.
