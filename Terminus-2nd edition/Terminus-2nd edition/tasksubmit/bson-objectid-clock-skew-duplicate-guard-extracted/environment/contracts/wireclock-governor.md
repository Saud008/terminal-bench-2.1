# Wireclock governor

Wireclock is a machine-bound ObjectId mint and intake governor.
It joins temporal minting, client_seq uniqueness claims, digest-hex batch authorization,
oidstore persistence, and path-scoped JSONL resume.
Contracts in this directory define externally observable requirements.

Verifier hosts may inject VERIFIER_SEED. Implementations must honor the contracts for any seed value;
seed only changes fixture machine identifiers and payload salts, not layout or denial rules.
Isolation overlays and the required exported package APIs are defined in isolation-overlay-contract.md.
