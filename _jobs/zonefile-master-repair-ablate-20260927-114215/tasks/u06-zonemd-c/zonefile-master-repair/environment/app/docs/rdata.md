# Record types

Input fields are tokens as described in `master-files.md`. Domain names in
RDATA are relative to the current origin like owner names, are stored in
canonical form and printed fully qualified. Numbers are plain decimal.

| Type | Code | Input fields | Printed as |
|------|------|--------------|------------|
| A | 1 | dotted-quad IPv4 address | `192.0.2.1` |
| NS | 2 | name | `ns1.example.com.` |
| CNAME | 5 | name | `target.example.com.` |
| SOA | 6 | mname rname serial refresh retry expire minimum | `mname. rname. serial refresh retry expire minimum` |
| PTR | 12 | name | `host.example.com.` |
| MX | 15 | preference (0-65535) name | `10 mail.example.com.` |
| TXT | 16 | one or more character-strings | `"part one" "part two"` |
| AAAA | 28 | IPv6 address | RFC 5952 form |
| SRV | 33 | priority weight port (0-65535 each) target | `10 60 5060 sip.example.com.` |
| ZONEMD | 63 | serial scheme hash-algorithm digest | see `zonemd.md` |
| CAA | 257 | flags (0-255) tag value | `0 issue "ca.example.net"` |

Notes:

- SOA `serial` is 0-4294967295. `refresh`, `retry`, `expire` and `minimum`
  accept the TTL syntax (`1h`, `2w`) and are printed in seconds.
- A: four decimal parts of 1-3 digits, 0-255 each.
- AAAA is printed in lowercase hex without leading zeros; the longest run
  of two or more all-zero groups (the first such run on a tie) becomes
  `::`. Embedded IPv4 notation is never printed.
- TXT and the CAA value accept quoted or unquoted tokens. A TXT
  character-string holds at most 255 octets after decoding escapes, a CAA
  value at most 1024.
- A CAA tag is 1-15 letters and digits and is printed as written.
- The wire form used for ordering is the RFC 1035 / RFC 3596 / RFC 2782 /
  RFC 8976 / RFC 8659 RDATA encoding of each type.
