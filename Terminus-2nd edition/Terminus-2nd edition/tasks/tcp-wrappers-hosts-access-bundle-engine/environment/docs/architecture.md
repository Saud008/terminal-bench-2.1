# Architecture

`hostsctl` is a Bash CLI that merges TCP wrapper rule bundles and decides whether a client IP may connect to a daemon.

Exports are written under `/app/output/`. Libraries live under `/app/lib/`. Contract docs are under `/app/docs/`.

## Library modules

| Module | Responsibility |
|--------|----------------|
| `common.sh` | Bundle paths, JSON export I/O, `bundle_fingerprint`, merge cache read/write, stale-cache detection |
| `parse.sh` | Fragment parsing (line continuations, daemon/client lists) |
| `aliases.sh` | Daemon alias normalization and rule matching |
| `cidr.sh` | Client pattern matching (`ALL`, `ALL EXCEPT`, IPv4/IPv6 CIDR) |
| `merge.sh` | Build merged export (allow rules before deny, sequential `index`, `stats`) |
| `publish.sh` | Staging artifact + publish seal; validate seal before writing merge cache |
| `decide.sh` | Two-pass allow-then-deny evaluation, canonical daemon in export |
| `replay.sh` | Session replay vs fresh `decide`; preserve checker exit code after `--export` |

`hostsctl` in `/app/bin/hostsctl` sources these modules; repair by editing `/app/lib/` only.
