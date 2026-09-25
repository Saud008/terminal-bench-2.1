# Exchange session ops workflow

Offline swarm-trade wantlist arena playfield for session sealing playtests.

## Playfield stages

1. **Admit** — ingest JSONL wantlist and block-exchange events from a fixture path.
2. **Gate** — enforce cancel-inflight, peer-credit dedupe, alias merge, idle flush, and priority scheduling per the sibling playfield contracts.
3. **Stage** — write `/app/state/want-snapshot.json` as the committed session witness.
4. **Seal** — publish session or metrics export JSON only from that staging snapshot.

There is no remote arena. Display tokens are public output keys; canonical multihash hex keys stay internal.

## Determinism

Pytest derives session names from `VERIFIER_SEED` and `TB3_SESSION_PREFIX` per `/app/docs/exchange-contract.md`. Held-out fixtures honor `TB3_FIXTURES_DIR` and ship under `/tests/hidden/exchange/` at grade time only. Reference replay in `tests/bitswap_trace_math.py` is independent of playfield sources.

## Runtime paths

Default staging, scratch, and example export paths are listed in `/app/docs/exchange-runtime-paths.md` and `/app/config/want-session.json`.
