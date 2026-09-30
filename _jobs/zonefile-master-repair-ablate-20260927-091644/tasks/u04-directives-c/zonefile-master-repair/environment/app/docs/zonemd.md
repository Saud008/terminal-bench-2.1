# ZONEMD

zonec fills in the zone digest record of RFC 8976 so that secondaries can
verify a transferred zone against the listing.

## Input

    owner [ttl] [IN] ZONEMD serial scheme hash-algorithm digest

`serial` is 0-4294967295, `scheme` and `hash-algorithm` are 0-255, and the
digest is 12 to 64 octets written in hex (either case), possibly split over
several tokens.

## The apex record

A ZONEMD record at the zone apex is a placeholder. The apex may hold at
most one ZONEMD record, and it must name scheme 1 (SIMPLE) and hash
algorithm 1 (SHA-384); anything else is an error at that record's line.
Its written serial and digest are ignored. In the listing its RDATA is
replaced by:

- serial: the serial of the zone's SOA record;
- scheme 1 and hash algorithm 1;
- digest: computed as described below.

Its TTL follows the normal rules of `master-files.md` and `output.md`.

ZONEMD records below the apex are ordinary records: printed as written and
included in the digest like any other record.

## Digest

The digest is SHA-384 over the concatenation of every record of the
listing except the apex ZONEMD record, in listing order (see `output.md`),
each in wire form:

    owner name   uncompressed, canonical case
    type         16 bits
    class        16 bits, IN = 1
    TTL          32 bits, the TTL printed in the listing
    RDLENGTH     16 bits
    RDATA        canonical wire form (see rdata.md)

All numbers are in network byte order. This is the SIMPLE scheme of
RFC 8976 section 3.3 applied to the listing.

## Printed form

    serial scheme hash-algorithm DIGEST

with the digest in upper-case hex without blanks, for example
`2026092701 1 1 3F09...`.
