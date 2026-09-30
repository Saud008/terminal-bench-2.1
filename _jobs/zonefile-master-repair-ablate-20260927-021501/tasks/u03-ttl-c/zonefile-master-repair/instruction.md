zonec (source in `/app`) is the small C tool our zone deploy pipeline uses to turn DNS master files into a canonical listing, and the diffs built from its output have been nonsense for a while. What people noticed so far:

- indented records right after an `$ORIGIN` line land on the wrong owner name
- a zone whose `$INCLUDE` lines use relative paths only compiles when zonec is started from inside the zone directory
- `smile IN TXT "ok :-)"` gets rejected with a parentheses error
- the record order doesn't look like DNS canonical order at all, the zone apex isn't even first

Probably not the only problems. The docs in `/app/docs` are the spec for what zonec accepts, how defaults are filled in, and what the listing looks like and in which order, so make zonec follow them exactly, also where they pick a different behavior than BIND. It will be run on zone files other than the ones in `/app/examples`.

Keep it plain C11 on the C library only (no running other programs), keep the command line, exit codes and diagnostic format from `/app/docs/zonec.1.md`, and `make` in `/app` has to keep working, including with `BUILD=` pointing at another directory.
