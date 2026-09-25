# Fixture catalog

Bundles under `/app/fixtures/bundles/`:

| Bundle | Notes |
|--------|-------|
| `office-edge` | IPv4 subnets, `ALL EXCEPT`, scanners |
| `dmz-ipv6` | Exact IPv6 host allow/deny (no prefix patterns) |
| `lab-aliases` | Daemon alias canonicalization |
| `except-trap` | `ALL EXCEPT` client patterns |
| `merge-order` | Allow-before-deny ordering |
| `wrap-join` | IPv4 CIDR allow (`198.51.100.0/24`) |

Field and export shapes are in `/app/docs/rule-format.md` and `/app/docs/export-schema.md`.

## Verifier probe address

`/app/fixtures/seeds.json` names the IPv4 prefix and daemon used for one dynamic `decide` check. The verifier sets `VERIFIER_SEED` (default: task id). Probe IP:

1. `digest = SHA-256(UTF-8 bytes of "{VERIFIER_SEED}:{probe_slot}")` hex string
2. `last_octet = (int(digest[0:2], 16) % 200) + 10`
3. Probe IP = `{base_ipv4}.{last_octet}` (fields from `seeds.json`)

Example slot `office` with `base_ipv4` `203.0.113` and daemon `sshd` on bundle `office-edge`.
