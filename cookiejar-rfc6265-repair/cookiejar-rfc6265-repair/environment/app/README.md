# crumbjar

crumbjar is the cookie store behind our HTTP session replayer. Recorded
sessions are turned into transcripts (a clock, the `Set-Cookie` headers each
response carried, and the requests that followed) and crumbjar replays them,
printing the `Cookie` header a browser-like user agent would have sent on
every request.

It has no dependencies outside the Rust standard library; `Cargo.toml`
lists none and `Cargo.lock` only has crumbjar itself.

```
cargo build --release
./target/release/crumbjar replay examples/basic.txt
```

Documentation:

- `docs/cli.md` - command line and output format
- `docs/transcript.md` - transcript syntax
- `docs/cookies.md` - which cookie specification crumbjar follows, and the
  choices it makes where that specification leaves room
- `docs/POLICY.md` - storage limits

Layout: `src/cookie` interprets a single `Set-Cookie` header, `src/jar` is
the store (storage, retrieval, eviction), `src/time` holds the cookie-date
parser and calendar code, `data/public_suffix.dat` is the public suffix list
compiled into the binary.
