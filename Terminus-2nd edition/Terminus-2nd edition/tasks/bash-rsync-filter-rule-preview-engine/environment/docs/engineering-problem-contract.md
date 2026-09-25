# Engineering problem contract

Operators run rsync with filter files and delete mode without a dry-run atlas. The preview engine must union sender inventory paths with receiver manifest paths, evaluate stacked filter rule chains per path, and emit transfer plus delete_risk verdicts before any sync executes.

Root cause gaps appear when rule precedence, cascade depth, prune flags, and receiver-only drift interact. Failure modes include wrong first-match indices, reversed cascade precedence, missing protected rows for receiver-only paths, and unstable atlas precedence.

The agent builds rsyncprev inventory, compile, and preview stages on the working baseline under /app. Contracts in sibling docs define filter tokens, cascade stack depth, prune semantics, delete risk for P and R tokens, and atlas JSON shape.
