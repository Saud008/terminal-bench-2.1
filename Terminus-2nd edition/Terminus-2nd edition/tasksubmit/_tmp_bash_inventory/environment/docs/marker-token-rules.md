# Vault markers

Values are vault encrypted when they start with $ANSIBLE_VAULT; after stripping leading and trailing whitespace.

YAML !vault tagged blocks with indented ciphertext lines are vault values. The first ciphertext line may include trailing whitespace that must be stripped before marker comparison.

Vault exposure findings occur when a key has a vault value in an earlier group layer but a plaintext value wins in effective vars for a host.
