# Midstate and Bundle Seal Formulas

All hashing uses SHA-256 over UTF-8 encoded text, expressed as lowercase hex
(`hashlib.sha256(text.encode("utf-8")).hexdigest()`).

## midstate_digest (written by `absorb`)

Computed over a newline-joined string built from the run's policy fields,
**in this exact field order**:

```
seed=<seed>
trace=<trace file basename>
adapter_power=<"on" or "off">
pairing_confirms=<int>
resume_tokens_cleared=<int>
gatt_resolve_count=<int>
reconnect_attempts=<int>
disconnect_reasons=<json.dumps(disconnect_reasons, separators=(",", ":"))>
```

`disconnect_reasons` is the JSON array of `{"mac", "reason",
"adapter_power"}` objects in the order they were recorded during absorb
(insertion order, not sorted). `midstate_digest` is the SHA-256 hex digest of
that newline-joined string.

## ledger_fingerprint (written by `seal`)

Computed over the midstate snapshot's `ledger_rows` array, in the **same order
the rows were appended during absorb** (insertion order — do not re-sort the
rows by event name, mac, or any other key). The full array is serialized in
one call to `json.dumps(ledger_rows, sort_keys=True, separators=(",", ":"))`.
`ledger_fingerprint` is the SHA-256 hex digest of that serialized string.

## bundle_seal (written by `seal`)

```
bundle_seal = sha256_hex(f"{midstate_digest}|{ledger_fingerprint}|{seed}")
```

using the `midstate_digest` read back from the midstate snapshot, the
`ledger_fingerprint` computed above, and the `seed` carried in the midstate
snapshot.

Sealing the same midstate snapshot twice without changing it must produce
byte-identical bundle output.
