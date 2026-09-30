# Master file input

zonec reads RFC 1035 master files (section 5) with the `$TTL` directive of
RFC 2308. This page lists the rules zonec implements. Where other
implementations disagree with each other, the rule written here is the one
zonec follows.

## Entries and tokens

- An entry is one line. `(` and `)` let an entry continue over several
  lines; line breaks between them count as blanks. Parentheses must balance
  within the entry.
- `;` starts a comment that runs to the end of the physical line.
- Tokens are separated by blanks and tabs. A token in double quotes may
  contain blanks, `;`, `(` and `)` as ordinary characters. A quoted string
  ends on the same line it starts.
- `\X` stands for the character X and `\DDD` (exactly three decimal digits,
  at most 255) for the octet with that value, both inside and outside
  quotes. An escaped `;`, `(`, `)` or `"` has no special meaning.
- Blank lines and lines holding only a comment are ignored.

## Directives

Directives start in the first column.

- `$ORIGIN name` sets the origin appended to relative names. A relative
  argument is itself taken relative to the current origin.
- `$TTL ttl` sets the default TTL (see below).
- `$INCLUDE file [origin]` reads another master file at this point (see
  below).

Any other `$` word in the first column is an error.

## Records

    [owner] [ttl] [class] type rdata...
    [owner] [class] [ttl] type rdata...

- The owner field is the first token of an entry that starts in the first
  column. `@` means the current origin, a name ending in `.` is absolute,
  any other name is relative to the current origin.
- An entry that starts with a blank or tab has no owner field and uses the
  owner of the previous record. `$ORIGIN` and `$TTL` do not change which
  owner that is. An indented entry before any record is an error.
- The only class accepted is `IN`; other class names are errors. Leaving
  the class out means `IN`.
- A TTL is a decimal number of seconds or a sequence of number/unit pairs
  (`w`, `d`, `h`, `m`, `s`, either case), for example `1h30m`. The maximum
  is 2147483647.
- Every owner must be the zone origin given with `-o` or a name below it.

## Default TTL

A record written with a TTL uses that TTL. For a record written without
one, the first of these that exists applies:

1. the value of the `$TTL` directive in effect;
2. the TTL most recently written on a record;
3. the MINIMUM field of the zone's SOA record, once the SOA record has
   been read (an SOA record without a TTL uses its own MINIMUM).

If none applies the record is an error. A TTL written on a record applies
to that record only; it never replaces the `$TTL` value.

## $INCLUDE

- A relative file name is taken relative to the directory of the file that
  contains the `$INCLUDE`, not the current working directory.
- The included file starts with the including file's state: its origin (or
  the origin given as the second argument, relative to the current origin),
  the owner of the previous record, and the default-TTL state (the `$TTL`
  value in effect and the TTL most recently written on a record).
- When the included file ends, all of that state reverts to what it was
  just before the `$INCLUDE` line. `$ORIGIN` and `$TTL` directives and
  record TTLs inside the included file therefore never affect the lines
  that follow the `$INCLUDE`.
- Includes may nest up to 8 levels.

## Domain names

- Escapes in names are decoded first; every rule below applies to the
  decoded octets.
- A label holds 1 to 63 octets. A name, in wire form including the root
  label, holds at most 255 octets. Empty labels (`a..b`) are errors.
- Names are case-insensitive. zonec stores every name in canonical form:
  octets `A` to `Z` become `a` to `z`, however they were written. Other
  octets are kept as they are.
