# fbdecode workspace

Rust CLI crate `fbdecode` decodes scene FlatBuffers into JSON. Schema lives in `schema/scene.fbs`; bundled binaries are under `fixtures/buffers/`.

Build:

```bash
cargo build --locked --release
```

Run:

```bash
fbdecode decode --schema /app/schema/scene.fbs --input /app/fixtures/buffers/shallow.bin
```
