# HTTP API (transit-mock)

Base URL: `http://127.0.0.1:8200`

## Load policy

`POST /v1/transit/keys/{name}/config`

```json
{"policy_file": "example.json"}
```

## Read policy / key

- `GET /v1/transit/keys/{name}/policy`
- `GET /v1/transit/keys/{name}`

## Rotate

`POST /v1/transit/keys/{name}/rotate`

Response header `X-Vault-Key-Version` is the new latest version.

## Encrypt / decrypt

`POST /v1/transit/keys/{name}/encrypt`

```json
{"plaintext": "<base64>", "context": "optional", "key_version": 0}
```

`key_version` of `0` selects the default for the key mode.

`POST /v1/transit/keys/{name}/decrypt`

```json
{"ciphertext": "v2::payload"}
```

## Batch encrypt

`POST /v1/transit/keys/{name}/encrypt/batch`

```json
{"batch_input": [{"plaintext": "<base64>", "context": ""}]}
```

Top-level `X-Vault-Key-Version` on batch responses reflects the version used for items (all items share the latest active encrypt version).

## Delete version

`DELETE /v1/transit/keys/{name}/versions/{version}`

## Soft halt

`POST /v1/transit/keys/{name}/halt`

```json
{"soft_rotation_halt_after_version": 2}
```

## Health

`GET /healthz` → `200 ok`
