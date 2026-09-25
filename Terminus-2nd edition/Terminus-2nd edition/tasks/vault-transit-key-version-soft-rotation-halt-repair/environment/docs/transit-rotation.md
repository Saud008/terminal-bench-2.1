# Transit key rotation contract

The in-container `transit-mock` service implements a reduced HashiCorp Vault Transit surface for regression testing. Authoritative behavior lives here and in `/app/docs/http-api.md`.

## Policy documents

Policy JSON files live under `/app/fixtures/policies/`. Loading a key via `POST /v1/transit/keys/{name}/config` reads the named file and initializes version **1**.

| Field | Meaning |
|-------|---------|
| `type` | Key algorithm label (opaque to tests) |
| `min_decryption_version` | Reject decrypt when ciphertext version is **strictly less** than this value |
| `deletion_allowed` | When `false`, version deletion must fail **before** ledger mutation |
| `convergent_encryption` | When `true`, encryption must use the **latest active** encrypt version (never pin version 1) |
| `soft_rotation_halt_after_version` | Optional default halt threshold copied onto the key at load time |

`GET /v1/transit/keys/{name}/policy` returns the parsed policy currently bound to the key. Parsed `min_decryption_version` must match the source file.

## Version ledger

- `POST .../rotate` increments `latest_version` and appends an active version entry.
- `DELETE .../versions/{n}` removes version **n** only when `deletion_allowed` is true; forbidden deletes leave the ledger unchanged.
- Batch encryption (`POST .../encrypt/batch`) must pick the **same** latest active encrypt version for **every** batch item. Item order or plaintext content must not change that pick.

## Soft rotation halt gate

`POST .../halt` sets `soft_rotation_halt_after_version`. Versions **less than or equal to** the halt threshold are **retired for encryption** (still decryptable when they satisfy `min_decryption_version`).

Encrypt or batch encrypt targeting a retired version returns **403** and response header `X-Vault-Halt: retired`.

## Response headers

Successful encrypt/decrypt responses include:

- `X-Vault-Key-Version` — version used for the operation
- `X-Vault-Min-Decryption-Version` — effective minimum decrypt version on the key

After code changes, rebuild and restart the service (`/app/scripts/verifier-rebuild.sh`).
