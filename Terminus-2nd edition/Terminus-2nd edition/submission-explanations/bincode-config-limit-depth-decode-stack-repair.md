# Submission explanations — bincode-config-limit-depth-decode-stack-repair

**Task folder:** tasks/bincode-config-limit-depth-decode-stack-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task is hard because six cooperating Rust modules under /app/crates/binlim-core/src must decode BLIM-framed payloads while enforcing configurable depth and byte budgets under four /app/docs contracts. Agents often fix varint parsing or enum traversal in isolation while byte accounting still skips length-prefix varint bytes on strings, depth frames charge before enum variant varints are read, or double_option nests consume two depth slots instead of one composite frame. Limit breaches frequently map to unexpected_eof when the byte budget hits zero mid-read even though limit-contract.md requires limit_exceeded with limit_kind depth or bytes. Non-minimal varints with redundant continuation bytes must reject as invalid_varint rather than silently accepting padded encodings. Partial fixes pass null and u32 fixtures but fail hidden tight-string byte traps, six-high enum depth bombs, or seed-generated enum towers that exhaust max_depth at runtime.

## Solution Explanation

The oracle replaces limit.rs, varint.rs, bytes.rs, visitor.rs, error.rs, and decode.rs under /app/crates/binlim-core/src with golden implementations, then rebuilds binlim-cli with cargo build. The decoder reads BLIM header bytes, charges every payload byte through a RefLimit tracker, validates canonical varints before use, and calls enter_composite only after vec count, enum variant, or double_option outer presence bytes are fully consumed per limit-contract.md. Nested enum payloads and double_option inner bodies share a single depth frame that restores on leave_composite, so Some(Some(null)) succeeds at max_depth 1. LimitExceeded maps to error_code limit_exceeded with the correct limit_kind and exit code 2, while true truncation with budget remaining stays unexpected_eof. Successful decodes write the documented JSON report to /app/output/decode-report.json with status ok, decoded value tree, and bytes_consumed matching independent reference accounting.

## Verification Explanation

Fourteen pytest functions drive binlim decode through subprocess after reset-state.sh clears /app/output, comparing decode-report.json to an embedded reference_decode implementation that mirrors the policy docs. Bundled fixtures under /app/fixtures/bin/ cover null and u32 success, redundant varint rejection, short strings, enum depth limits, and double_option depth framing. Hidden fixtures under /tests/hidden_fixtures/binlim/ exercise tight string byte budgets where the length-prefix varint must count toward max_bytes, six-high enum chains with seed-dependent max_depth, and triple-byte redundant varint encodings. Runtime-generated enum towers built from VERIFIER_SEED block hard-coded depth answers. Each test asserts status, error_code, limit_kind, value tree on success, bytes_consumed parity, and CLI exit codes 0 for ok, 2 for limit_exceeded, 3 for invalid_varint or invalid_tag, and 4 for unexpected_eof.
