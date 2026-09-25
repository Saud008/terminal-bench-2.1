The `oasctl` CLI under `/app/cmd/oasctl` validates request-body payloads against an OpenAPI 3 document at `/app/fixtures/openapi.yaml`. It dereferences request-body schemas, replays payload fixtures from `/app/fixtures/payloads/` according to `/app/config/oasctl.json`, and writes `/app/output/validation-report.json`. Dereference, validation, payload selection, and report layout are defined in `/app/docs/openapi-contract.md`; field types, ordering, stats, and exact error message templates are in `/app/docs/report-schema.md`. Payload and spec formats are in `/app/docs/payload-format.md` and `/app/docs/spec-format.md`.

This is an offline schema contract — not a live HTTP server. Exit code `0` on success; `2` on usage or I/O errors. Rebuild from `/app` after changes (`go build -mod=readonly -o /usr/local/bin/oasctl ./cmd/oasctl`).

Do not edit `/app/docs/`, anything under `/app/fixtures/`, `/app/config/oasctl.json`, or anything under `/tests`.
