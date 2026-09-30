# Canonical listing

On success zonec writes the whole zone to stdout, one record per line:

    <owner><TAB><ttl><TAB>IN<TAB><TYPE><TAB><rdata>

- `owner` is the fully qualified name in canonical form, with a trailing
  dot.
- `ttl` is decimal seconds.
- `TYPE` is the upper-case mnemonic.
- `rdata` is described per type in `rdata.md`.

Nothing else is printed: no comments, no directives, no blank lines.

## Names

Labels are printed octet by octet:

- `.` `\` `"` `(` `)` `;` `@` `$` are printed with a backslash in front;
- octets up to 0x20 (space included) and from 0x7f up are printed as
  `\DDD` with three decimal digits;
- everything else is printed as is.

The root name is printed as `.`.

## Character-strings

Printed in double quotes. `"` and `\` get a backslash in front, octets
below 0x20 and from 0x7f up are printed as `\DDD`, everything else
(space included) as is.

## Duplicates

Records with the same owner, type and RDATA are one record. Only the first
one in input order is kept.

## RRset TTL

All records of one RRset (same owner and type) are printed with the same
TTL: the TTL of the RRset's first record in input order. Input order is the
order in which records are read, with included files read at the point of
their `$INCLUDE`.

## Order

Records are sorted by:

1. owner name, in the canonical DNS name order of RFC 4034 section 6.1:
   names are compared label by label starting from the root label, each
   label compared as an unsigned octet string on its canonical form, and a
   label that is a prefix of another sorts first (so a name sorts before
   every name below it);
2. type code, numerically (A=1 first, CAA=257 last);
3. RDATA in canonical wire form (names uncompressed and lowercased),
   compared as unsigned octet strings, a prefix sorting first.
