# Submission explanations — bash-openssh-authorized-principals-attestor

**Task folder:** tasks/bash-openssh-authorized-principals-attestor/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must implement a fleet OpenSSH certificate principals attestor that ingests principals files, CA keys, and KRL revocations into a trust ledger, then emits a signed principals attestation bundle for session probes. The hard part is the interaction between Match block scope selection, deny-line precedence, CA scope gates, wildcard policy, and revocation ordering. Fixing one module can pass bundled probes while scoped global fallback, hidden verifier fixtures, or attest-only scope rules still fail. Bundle seal math binds ordered binding seals, so partial attest logic breaks the top-level digest even when individual verdicts look plausible.

## Solution Explanation

The oracle patches seven bash modules under /app/lib, rebuilds sshap, and runs ingest then attest through the real CLI. Ingest must normalize KRL fingerprints and ledger rows in the documented order. Attest must resolve Match scope, apply wildcard and CA gates, rank principals correctly, and write session_bindings plus bundle_seal to the attestation bundle path. The witness binder must check revocation before wildcard policy and must not let global principals leak into scoped Match contexts.

## Verification Explanation

test.sh rebuilds sshap before pytest. Tests call /usr/local/bin/sshap via subprocess for ingest and attest. The verifier oracle recomputes ledger fingerprints, scope resolution, binding seals, and bundle seals from fixtures so agents cannot hardcode JSON. Hidden probes under the extra verifier fixture directory exercise alternate match and probe paths with different failure modes than bundled sessions. Repeated attest on an unchanged ledger must produce identical bundle bytes.
