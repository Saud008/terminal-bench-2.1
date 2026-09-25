# Platform rubric — go-dpop-jkt-pin-admission-gate

**Task folder:** tasks/go-dpop-jkt-pin-admission-gate/
**Written:** 2026-07-16T15:15:23Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent opens DPoP sessions with vault HMAC bind tickets and pins jkt at session open, +3
Agent verifies proofs with SHA-256 jkt thumbprints matching the pin registry, +3
Agent enforces case-insensitive htm and exact htu binding on /gate/proof/check, +3
Agent admits iat within bidirectional skew and denies jti replays inside the nonce window, +3
Agent stages /app/state/chainhead.json then seals /app/output/deny-ledger.json with matching totals, +3
Agent honors JKTADMIT_PIN_DIR for hidden pin registries under verifier fixtures, +2
Agent rebuilds jktadmit with go build after editing jktpin/proofparse/jtiledger/chainhead/auditseal packages, +2
Agent leaves protected gateway wiring and /app/docs contracts unchanged, +1
Agent only patches jkt while htm case folding and replay ledger remain wrong, -3
Agent hardcodes deny-ledger.json without running open/check/commit HTTP cycle, -3
Agent edits tests or /opt/verifier-fixtures to weaken hidden pin registry checks, -5
