# Merkle tree over chunk hashes

`cdcctl roll` builds a binary merkle tree over the **chunk content hashes** (`chunks[].hash`) in emission order. Each `hash` is a lowercase hex-encoded SHA-256 digest of the chunk bytes (64 ASCII hex characters).

## Leaf level

Leaves are the chunk `hash` strings in the order chunks are emitted during the roll.

## Parent nodes

Walk the current level left to right, pairing adjacent siblings:

1. If the level has an odd number of nodes, **duplicate the last leaf** before pairing.
2. For each pair `(left, right)`, the parent digest is:

```text
parent_hex = sha256_hex( UTF-8(left_hex) || UTF-8(right_hex) )
```

**Important:** `left_hex` and `right_hex` are the **hex text strings** (64-byte ASCII each), concatenated as UTF-8 bytes and hashed. Do **not** decode the sibling digests from hex into 32-byte binary values before hashing.

Example: if `left_hex = "abc..."` and `right_hex = "def..."`, hash the 128-byte ASCII concatenation, not `decode_hex(left) || decode_hex(right)`.

3. Repeat until one root hex string remains. An empty chunk list uses `sha256_hex("")`.

## Ordering

Pairing is always **left then right** at each level. Reordering chunk hashes changes the root.
