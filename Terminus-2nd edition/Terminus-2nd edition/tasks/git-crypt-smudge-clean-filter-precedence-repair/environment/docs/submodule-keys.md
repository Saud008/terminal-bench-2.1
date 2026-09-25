# Submodule key resolution

Key files live at ROOT/.gcrypt/keys/default relative to the --repo argument, never relative to the process current working directory.

Format:

```
key_id=HEX8
material=HEX64
```

key_id is eight lowercase hex digits. material is 32 bytes as 64 hex digits used for XOR stream encryption.

When tests run smudge or clean inside a subdirectory of ROOT, key lookup must still open ROOT/.gcrypt/keys/default.

Parent repo keys must not be used when --repo is a submodule fixture root.
