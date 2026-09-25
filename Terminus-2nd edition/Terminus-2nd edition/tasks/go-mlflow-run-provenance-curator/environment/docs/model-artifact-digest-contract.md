# Model artifact digest contract

Each model artifact entry carries rel_path and content (UTF-8 string body as stored in the scenario).

Compute digest closure as SHA-256 over the canonical string formed by rel_path, a single newline character, then content bytes. Express the digest as lowercase hexadecimal.

When comparing artifacts across runs, use the digest only. rel_path must be normalized by trimming a leading ./ prefix before digest input.

Sort artifact digests lexicographically by rel_path when emitting certificate lists.
