# Shot histogram normalization

The qasmenv envelope compute stage reads histogram rows from /app/state/cal-staging.json and produces per-qubit probability vectors before mitigation.

Each histogram row carries a qubit label and a counts array of non-negative integers representing measured outcome bins for that qubit.

Normalization divides every count in a row by that row's own sum. Each qubit's resulting probabilities must sum to exactly 1.0 within floating tolerance 1e-9.

Rows must never be normalized using a global sum across all qubits or all bins. Cross-qubit pooling produces invalid shot-noise envelopes.

The normalized vectors are stored in the ledger under normalized_probs keyed by qubit label preserving the staging qubit order.
