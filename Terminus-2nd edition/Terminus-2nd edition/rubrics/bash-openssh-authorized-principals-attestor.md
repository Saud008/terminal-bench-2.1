# Platform rubric — bash-openssh-authorized-principals-attestor

**Task folder:** tasks/bash-openssh-authorized-principals-attestor/

Agent ingests principals, CA keys, and KRL revocations into trust_ledger.json via sshap ingest, +3
Agent resolves Match block scope before ranking principals for each session probe, +3
Agent applies exclamation deny lines before allow principals per scope, +3
Agent enforces cert-authority principal scope when signed_by_ca is true, +3
Agent rejects revoked key fingerprints before wildcard or principal matching, +3
Agent emits principals_attestation_bundle.json with session_bindings sorted by probe_id, +3
Agent computes bundle_seal from ordered binding_seal digests, +3
Agent honors TB3_MATCH_DIR and TB3_PROBES_FILE overrides during attest, +2
Agent rebuilds sshap via rebuild-sshap.sh before subprocess verifier runs, +2
Agent keeps attest idempotent when ledger bytes are unchanged, +2
Agent lets global principals satisfy scoped Match sessions, -3
Agent checks wildcard policy before KRL revocation lookup, -3
Agent includes non-global principals when Match scope is global, -3
Agent hardcodes attestation JSON instead of running witness binder logic, -5
