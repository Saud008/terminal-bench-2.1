# Zone file format

Zone files use BIND-like directives and resource records.

## Directives

$ORIGIN sets the origin for relative owners. $TTL sets default TTL for following records until changed. $INCLUDE path pulls another file inline at the directive location.

## Resource records

Format: owner [ttl] IN type rdata

Comments start with semicolon. Blank lines are ignored.

## SOA rdata

SOA rdata begins with serial integer followed by refresh retry expire minimum fields.

## NSEC rdata

NSEC rdata is next-owner followed by type bitmap tokens.
