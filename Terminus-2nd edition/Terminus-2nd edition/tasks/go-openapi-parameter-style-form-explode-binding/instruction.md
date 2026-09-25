API-edge security operators need a host-local parameter trust-policy admission control plane at `/usr/local/bin/paramgate`. The plane admits inbound catalog and admin traffic against merged OpenAPI trust contracts, evaluates style/explode authenticity and required-field trust gates over query, path, header, and JSON body fields, stages a tamper-evident witness snapshot at `/app/state/bind-snapshot.json`, and publishes policy-checked JSON only when those bindings match the site integrity contract—without an outbound network step or remote download. This is a security trust-policy admission and sealed-witness attestation workflow: keep style/explode authenticity, required-parameter admission, canonical bind order, tamper-evident staging, and witness-backed HTTP export aligned. It is not a generic Go OpenAPI binder, API-framework rebuild, pytest harness, or CI tooling exercise.

At startup the gate loads `/app/fixtures/openapi-base.yaml` and merges `/app/fixtures/admin-paths.yaml` per `/app/config/paramgate.yaml`. Admin routes under `/v1/admin/` come from that extension fragment. Catalog-only policy evaluation is not sufficient for full trust coverage.

Successful attestation must canonicalize bound parameters, seal them into `/app/state/bind-snapshot.json`, and return HTTP 200 with a JSON payload whose `params` field is published from that witness snapshot (and `body` for `POST /v1/catalog/notes`). Client trust-policy violations return HTTP 400 with `status` `invalid` and a reason code. Reserve HTTP 500 for unexpected internal faults only.

Policy modules under `/app/internal/bind/` implement ingest (query/path/header/body binding), canonicalization, staging, and export publishing. `wrap.go` retains legacy CLI helpers and is not authoritative for HTTP admission. After edits under `/app/internal/bind/`, leave `/usr/local/bin/paramgate` current (the verifier may invoke `/app/scripts/verifier-rebuild.sh`).

Security contracts under `/app/docs/`:

- parameter policy attestation workflow: `/app/docs/parameter-policy-attestation.md`
- style and explode authenticity for query, path, header, and body fields: `/app/docs/param-binding-contract.md`
- canonical bind order for witness digests: `/app/docs/canonical-bind-order.md`
- tamper-evident witness snapshot layout: `/app/docs/bind-snapshot.md`
- HTTP admission surface and reason codes: `/app/docs/bind-api.md`

Bundled fixtures live under `/app/fixtures`. Hidden verifier trees may appear under `/opt/verifier-fixtures/`. Environment variable `TB3_FIXTURE_DIR` may redirect that fixture root during hidden policy attestation probes. Do not edit `/app/docs/`, `/app/fixtures/`, `/app/config/`, or anything under `/tests`.
