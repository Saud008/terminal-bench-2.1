# Rule format

TCP wrapper fragments use one rule per line:

```text
daemon_list : client_list
```

- Lines starting with `#` are comments; blank lines are ignored.
- `daemon_list` is a comma-separated list of service names, or `ALL`.
- `client_list` is a comma-separated list of client patterns.
- Trailing `\` continues the line: drop the backslash, trim trailing whitespace on the continued portion, then append the next physical line after trimming its leading whitespace. Do not insert extra spaces between the joined parts (a CIDR such as `198.51.100.0/24` may be split across lines).

Example continuation (not used in bundled fixtures, but valid in real fragments):

```text
sshd: 198.51.100. \
      0/24
```

must parse as client pattern `198.51.100.0/24`, not `198.51.100. 0/24` or two separate tokens.

## Client patterns

| Pattern | Meaning |
|---------|---------|
| Dotted IPv4 | Exact host or prefix-less address |
| `n.n.n.n/m` | IPv4 CIDR |
| `xxxx:.../m` | IPv6 CIDR (hex groups, lowercase normalized in exports) |
| `ALL` | Any client |
| `ALL EXCEPT pat ...` | Any client not matching any pattern after `EXCEPT` |

Patterns are matched against the **connection IP string** passed to `hostsctl decide` (already normalized: no brackets, lowercase IPv6).

## Daemon names

Service names are compared after applying `/app/docs/daemon-aliases.md` for the bundle. Lookup is **case-insensitive** on both rule daemons and the `--daemon` argument.
