# Engineering problem contract — libp2p-bitswap-wantlist-cancel-repair

Identity token 7ed40b5571 anchors this bitswap wantlist cancel task in the corpus.

## Root cause envelope

The baseline bswapd ingest path treats display CIDs as map keys, credits ledger on block_start, and drops cancel tombstones after block_done. Agents must rebuild canonical-key want tracking, export-from-staging discipline, and delivery versus ledger dedupe rules documented under /app/docs/bitswap-display-cid-rules.md.

## Failure modes verified

Alias merge must collapse duplicate canonical blocks while preserving first-registered display CIDs. Cancel during in-flight must not drop partial buffers before block_done. Idle ticks must flush wants and partial state at the documented threshold. Ledger credit must apply once per peer and display cid while delivered rows append for every block_done.

## Determinism gate

Pytest derives session names from VERIFIER_SEED and TB3_SESSION_PREFIX per /app/docs/bitswap-contract.md. Hidden fixtures honor TB3_FIXTURES_DIR. Reference replay in tests/bitswap_trace_math.py is independent of Go sources.

## Runtime paths

Default staging, scratch, and example export paths are listed in /app/docs/bitswap-runtime-paths.md and /app/config/bitswap-session.json.
