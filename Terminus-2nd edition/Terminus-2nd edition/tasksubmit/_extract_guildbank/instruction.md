Guild-treasury security operators need a host-local withdraw-admission and audit-attestation control plane at /usr/local/bin/guildbankd. The plane admits offline vault and gold mutations into a tamper-evident SQLite trust journal, evaluates stack-split authenticity, gold withdraw admission, bound transfer-out refusal, concurrent rollback integrity, and interest-journal anti-replay gates, then publishes a digest-sealed guild audit only when ledger rows match the attestation contracts—without a remote treasury host or outbound network step. This is a security treasury-attestation and sealed-audit workflow: keep withdraw authenticity, bound-item transfer blocks, concurrent rollback integrity, interest anti-replay, and digest-bound audit attestation aligned. It is not a generic Go HTTP bank engine, daemon rebuild, pytest harness, or CI tooling exercise.

Security contracts under /app/docs/:

- withdraw and transfer admission surface: /app/docs/bank-contract.md
- partial stack-split authenticity: /app/docs/stack-split.md
- concurrent gold-draw rollback integrity: /app/docs/concurrency.md
- audit row ordering gates: /app/docs/audit-order.md
- bound-item transfer-out refusal: /app/docs/bound-items.md
- interest-journal anti-replay: /app/docs/interest-journal.md
- digest-sealed audit export: /app/docs/export-schema.md
- fixture inventory: /app/docs/fixture-catalog.md

guildbankd serve --config /app/config/guildbank.json must host the treasury attestation surface on port 8080. Bootstrap, vault stack deposit, gold and stack withdraw, transfer-out, interest run/replay, and audit export must obey the contracts above. Partial stack withdraw must leave remnant vault rows and withdraw_slices consistent with /app/docs/stack-split.md. Concurrent gold draws must serialize under the concurrency contract without orphaned audit rows. Interest crash replay must remain idempotent per /app/docs/interest-journal.md. Export must seal /app/output/guild-audit.json only when ledger rows match /app/docs/export-schema.md.

Binary path: /usr/local/bin/guildbankd. Optional header X-Test-Mono-Ms pins the monotonic clock for deterministic attestation windows. Missing required fields and conflict cases such as insufficient gold, unknown stacks, bound transfer-out, or invalid quantities must refuse mutation per /app/docs/bank-contract.md. Treasury staging lives at /app/work/guildbank.db. Do not edit /app/docs/, /app/config/, /app/fixtures/, or /tests/. Do not run apt-get, pip install, or other network installs.
