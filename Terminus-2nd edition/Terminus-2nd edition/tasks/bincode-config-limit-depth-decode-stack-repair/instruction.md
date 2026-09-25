The binlim decoder under /app/crates/binlim-cli reads BLIM-framed payloads and must enforce configurable recursion depth and byte budgets during decode. Today it accepts depth bombs, miscounts bytes on length prefixes, tolerates non-canonical varints, and reports limit breaches with the wrong error code.

Repair the decoder stack under /app/crates/binlim-core/src so binlim decode honors the contracts in /app/docs/wire-format.md, /app/docs/limit-contract.md, /app/docs/cli-surface.md, and /app/docs/error-codes.md. After your fix, binlim decode --input PATH --output /app/output/decode-report.json --max-depth N --max-bytes N must produce the documented JSON report shape, canonical varint rejection, correct depth accounting for nested enums and double-wrapped options, and limit breaches surfaced as error_code limit_exceeded (not unexpected_eof).

Do not edit files under /app/docs/ or /app/fixtures/bin/.
