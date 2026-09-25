# slsacip

slsacip is the Sigstore ClusterImagePolicy attestation admission governor.
It binds Fulcio-style trust roots to offline Cosign attestation envelopes
and admits or denies image-pull tickets under digest-deny pins, revocation
seals, predicate allowlists, builder authz, and N-of-M quorum policy.

## Build

```sh
go build -o /usr/local/bin/slsacip ./cmd/slsacip
```

## Usage

```sh
slsacip attest \
  --config /app/config/slsacip.json \
  --pulls  /app/fixtures/pull-waves/wave-north.jsonl \
  --output /app/output/slsa-admission-ledger.json
```

`attest` loads the configured trust roots, policy tiers, and attestation
envelopes, selects and merges the configured policy tiers by seed, evaluates
every pull request in `--pulls`, stages a witness snapshot at
`/app/state/slsacip/trust-witness.json`, and writes the digest-sealed
admission ledger to `--output`.

## Contracts

The trust bind, revocation, predicate, builder authz, quorum, witness, and
seal contracts this binary must satisfy are documented in `docs/`:

- `docs/fulcio-root-bind.md`
- `docs/revoke-halfopen.md`
- `docs/predicate-exact-allow.md`
- `docs/builder-glob-authz.md`
- `docs/digest-pin-deny.md`
- `docs/quorum-n-of-m.md`
- `docs/trust-witness-format.md`
- `docs/ledger-seal-format.md`

## Layout

- `cmd/slsacip` — CLI entrypoint (`attest` subcommand)
- `internal/ciptypes` — shared types
- `internal/cipcfg` — config JSON loader
- `internal/cipload` — trust root, policy tier, envelope, and pull loaders
- `internal/cipemit` — ledger writer
- `internal/rootbind` — anchored glob matching and trust binding
- `internal/predallow` — predicate-type allowlist gate
- `internal/buildergate` — builder identity deny/require gate
- `internal/pindeny` — digest-deny pin gate
- `internal/revokewin` — revocation window gate
- `internal/quorumadmit` — tier selection/merge and per-pull evaluation
- `internal/witnesswrite` — witness snapshot fingerprints
- `internal/sealhex` — audit digest sealing
- `internal/admitrun` — end-to-end wiring for `attest`
