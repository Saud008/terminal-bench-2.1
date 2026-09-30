# Command line

```
crumbjar replay <transcript>
crumbjar replay -
crumbjar --version
```

`replay` reads a transcript (see `transcript.md`) from the named file, or
from standard input when the argument is `-`, and executes its commands in
order against an empty cookie store.

## Output

Everything goes to standard output, one line per event, in transcript order.

A `get` command prints the request URL exactly as written in the
transcript, a single TAB, and the value of the `Cookie` header the request
carries: `name=value` pairs joined with `"; "` (semicolon, space). When no
cookie applies, the line is the URL followed by the TAB and nothing else.

```
https://www.example.com/cart	sid=31d4d96e; lang=en-US
https://static.example.net/logo.png	
```

A `dump` command prints a header line followed by one line per cookie in the
store that has not expired at the current clock:

```
-- jar @<clock>: <n> cookie(s)
<domain>	<path>	<name>=<value>	<flags>	<expiry>	<created>	<accessed>
```

Fields are separated by a single TAB.

- `domain`, `path`, `name`, `value`: the cookie's stored fields.
- `flags`: the set flags among `host-only`, `secure`, `httponly`, in that
  order, joined with commas; `-` when none is set.
- `expiry`: `session` for a non-persistent cookie, otherwise its
  expiry-time in seconds since the epoch.
- `created`, `accessed`: clock value of the cookie's creation-time and
  last-access-time.

Cookie lines are sorted by domain, then path, then name (byte order). A
`dump` does not count as an access.

## Exit status

- 0: the transcript was replayed.
- 1: the transcript could not be read or has a malformed line; a message of
  the form `crumbjar: line <n>: <reason>` goes to standard error and nothing
  is replayed.
- 2: bad command line.
