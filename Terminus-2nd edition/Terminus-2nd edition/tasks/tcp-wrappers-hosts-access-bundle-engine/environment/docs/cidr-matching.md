# Client address patterns

`hostsctl decide` receives a single normalized IP string. Client patterns in rule fragments may include:

- dotted IPv4 host addresses
- IPv4 CIDR (`a.b.c.d/prefix`)
- IPv6 CIDR (hex groups, optional `::` compression, `/prefix`)
- `ALL`
- `ALL EXCEPT` followed by one or more sub-patterns

Syntax and comma-list rules are in `/app/docs/rule-format.md`. IPv6 addresses in exports use lowercase hex.

## CIDR membership

A connection IP matches a CIDR pattern when it is a member of that network using standard library semantics (same result as Python 3: `ipaddress.ip_address(ip) in ipaddress.ip_network(pattern, strict=False)`). Apply this for both IPv4 and IPv6. Do not approximate IPv6 with prefix-length nibble truncation or other shortcuts.
