Our session replayer keeps its cookies in crumbjar (Rust, source in `/app`), and replays have been sending the wrong cookies. So far:

- a login cookie set by `https://example.com/` with no Domain attribute also goes out to `https://api.example.com/`
- cookies set by `https://help.example.net/kb/articles/123` don't come back on `https://help.example.net/kb/articles`
- some cookies with perfectly good far-future Expires dates are never stored
- when a server refreshes a cookie's value, the cookie moves to the end of the Cookie header

I doubt that's all of it. crumbjar is supposed to be the user-agent side of RFC 6265 as published in 2011 (not the 6265bis drafts), with the per-site limit in `/app/docs/POLICY.md` on top. `/app/docs` has the transcript and output formats and the choices crumbjar makes where the RFC leaves room; treat it as the spec. Fix crumbjar so `crumbjar replay` prints exactly what such a jar would, for transcripts other than the ones above and in `/app/examples`.

Keep it std-only Rust (no crates, no `unsafe`, don't run other programs), don't change the command line or output format in `/app/docs/cli.md`, and a plain `cargo build --release` in `/app` has to keep working.
