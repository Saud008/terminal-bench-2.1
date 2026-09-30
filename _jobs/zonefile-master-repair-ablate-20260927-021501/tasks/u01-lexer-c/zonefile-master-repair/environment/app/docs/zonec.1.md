# zonec(1)

## Synopsis

    zonec -o ORIGIN FILE
    zonec -h

## Description

Reads the master file FILE, and every file it includes, as the zone
ORIGIN and writes the canonical listing described in `output.md` to
stdout.

ORIGIN is always taken as absolute; the trailing dot is optional.

## Exit status

- 0: the zone was compiled and the listing written.
- 1: the zone has an error. One diagnostic line is written to stderr and
  nothing is written to stdout.
- 2: bad command line.

## Diagnostics

Errors found in a file are reported as

    FILE:LINE: message

where FILE is the path zonec opened (for included files: the path after
resolving it against the including file's directory) and LINE is the
physical line the offending entry starts on. For an `$INCLUDE` whose file
cannot be opened, the position is that of the `$INCLUDE` line.

Errors that belong to no line (a missing SOA record, an unreadable FILE)
are reported as `FILE: message`.

The wording of the message is not part of the interface.
