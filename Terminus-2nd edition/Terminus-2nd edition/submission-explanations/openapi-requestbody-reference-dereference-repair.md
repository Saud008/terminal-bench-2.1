# Submission explanations — openapi-requestbody-reference-dereference-repair

**Task folder:** tasks/openapi-requestbody-reference-dereference-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must make the offline `oasctl validate` CLI dereference OpenAPI request-body schemas and validate JSON payload fixtures against four `/app/docs` contracts, not just patch one helper. Reference following is broken at several layers: `$ref` chains stop after a single hop so inherited required fields from `BaseRecord` never surface, cyclic `Contact`/`profile` graphs never increment `cycles_seen`, and `allOf` merge keeps the first fragment’s property definitions instead of letting later fragments override them. Discriminator handling looks up subschemas by raw discriminator value rather than the `mapping` table, so unknown pet kinds fail silently and `additionalProperties: false` on `CatBody` is never enforced. Nullable `[string, "null"]` unions reject JSON `null`, and default injection runs too early by marking defaulted properties as required. Partial fixes often pass simple pet name checks while still failing employee `employeeId` requirements, seed-driven payload subset ordering, or the exact error templates in `report-schema.md`.

## Solution Explanation

The oracle copies seven golden implementations into `/app/internal/deref/` — `ref.go`, `cycle.go`, `merge.go`, `nullable.go`, `discriminator.go`, `defaults.go`, and `resolve.go` — then rebuilds `oasctl` with `go build`. Dereference walks internal `#/components/schemas` refs with an active stack, records cycles as empty object branches, merges `allOf` fragments with later overrides and unioned `required` arrays, and applies discriminator `mapping` merges only when the payload carries the discriminator property. Defaults fill missing properties after merge, nullable unions accept `null`, and validation emits the documented message strings. The CLI still selects payloads via the config seed bitmask and Fisher–Yates shuffle from `openapi-contract.md`, then writes the full matrix to `/app/output/validation-report.json` with per-file `valid`, `errors`, and `cycles_seen` fields plus aggregate `stats`.

## Verification Explanation

Eleven pytest functions rebuild the Go binary after `reset-state.sh`, invoke `oasctl validate` as a subprocess, and compare output to an independent `reference_validator.py` implementation that re-parses the YAML spec and replays the same seed selection logic. Bundled checks cover fixture SHA-256 integrity, full-report equality, nullable email acceptance, discriminator merge with `extra-field-cat` rejection, multi-hop ref required `id`, unknown discriminator errors, `allOf` employee records, cyclic contact `cycles_seen`, and stats of six valid versus five invalid payloads on the default seed. A second seed (`oas-seed-64`) verifies bitmask subset selection and ordering without hard-coding filenames. Every behavioral assertion runs through the compiled CLI path so agents cannot satisfy tests by editing JSON by hand.
