# Bitswap session ops workflow

Host-local bswapd wantlist session control plane for offline bitswap session administration.

## Control-plane stages

1. **Admit** — ingest JSONL wantlist and block-exchange events from a fixture path.
2. **Gate** — enforce cancel-inflight, peer-credit dedupe, alias merge, idle flush, and priority scheduling per the sibling ops contracts.
3. **Stage** — write `/app/state/bitswap-snapshot.json` as the committed session witness.
4. **Seal** — publish session or metrics export JSON only from that staging snapshot.

There is no remote swarm. Display CIDs are public output keys; canonical multihash hex keys stay internal.

## Determinism

Pytest derives session names from `VERIFIER_SEED` and `TB3_SESSION_PREFIX` per `/app/docs/bitswap-contract.md`. Hidden fixtures honor `TB3_FIXTURES_DIR`. Reference replay in `tests/bitswap_trace_math.py` is independent of Go sources.

## Runtime paths

Default staging, scratch, and example export paths are listed in `/app/docs/bitswap-runtime-paths.md` and `/app/config/bitswap-session.json`.
