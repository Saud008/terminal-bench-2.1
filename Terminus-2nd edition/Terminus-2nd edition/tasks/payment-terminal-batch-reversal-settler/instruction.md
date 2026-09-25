Payment-terminal settlement integrity officers must deliver termsetctl at /app/bin/termsetctl as a host-local trust admission gate that admits signed terminal transcripts into a tamper-evident batch journal and publishes sealed settlement bundles only after reversal-linkage, cutoff-window, sequence-guard, and terminal-key HMAC attestation gates pass. There is no remote acquirer hop and no outbound network step. Funds release must not proceed without a journal_digest-bound settlement-witness.hmac that matches the integrity contract. This is a settlement trust-attestation and HMAC seal control plane, not a generic service repair exercise.

Trust-policy contracts under /app/docs/cli-surface.md, /app/docs/batch-journal-contract.md, /app/docs/reversal-pairing-contract.md, /app/docs/cutoff-window-contract.md, and /app/docs/seal-hmac-contract.md define CLI verbs, journal line digests and emission order, reversal linkage eligibility, inclusive cutoff boundaries, and HMAC attestation derivation over the journal digest using terminal batch keys.

termsetctl compile-journal --scenario <name> [--fixture-dir <path>] must normalize transaction state, enforce reversal pairing and cutoff admission, assign monotonic sequence guards, and stage /app/state/batch-journal.jsonl plus /app/state/journal-meta.json. Public scenarios sit under /app/fixtures (for example /app/fixtures/scenarios/clean-settle.json); callers may also supply an alternate --fixture-dir.

termsetctl seal-bundle --scenario <name> [--fixture-dir <path>] must publish /app/output/settlement-bundle.json and /app/output/settlement-witness.hmac only from the compiled journal using the scenario terminal batch key per seal-hmac-contract.md. The witness must attest journal_digest bytes, not the marshaled bundle body.

Requirements:
- The decoy receipt formatter under internal/decoy/ must not influence compile-journal or seal-bundle trust decisions.
- Leave /app/docs/ and /app/fixtures/ unchanged.
- Settlement artifacts under /app/state and /app/output must remain wipeable between independent trust evaluations via /app/scripts/reset-state.sh.
