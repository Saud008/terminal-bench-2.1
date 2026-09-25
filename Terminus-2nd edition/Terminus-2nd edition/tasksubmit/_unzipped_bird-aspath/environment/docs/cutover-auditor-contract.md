# Cutover cutover contract

bgpcut cutover loads a peer inventory, applies peer-id salt, evaluates every peer route in wave order, writes /app/state/cutover-ledger.json, then seals the cutover report to --output.

The sealed report must be derived from the ledger bytes (peer_order, rows, wave_aborted), not by re-sorting peers or rows during seal.
