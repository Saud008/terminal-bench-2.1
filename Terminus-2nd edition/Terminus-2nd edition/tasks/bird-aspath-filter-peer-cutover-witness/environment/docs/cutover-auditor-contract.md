# Cutover auditor contract

bgpcut cutover loads a peer inventory, applies peer-id salt, evaluates every peer route in wave order, writes /app/state/cutover-ledger.json, then seals the cutover report to --output.

Ledger and report field names are in ledger-and-seal.md. Wave order, filter inheritance, path match, rewrite, MED, abort, and seal rules are stated in the task instruction.
