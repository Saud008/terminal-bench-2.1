# bag-audit (ROS2 bag QoS)

Offline rosbag2-style bundle auditor with gap fill and deadline export. Contracts: `/app/docs/`.

## Environment

| Item | Location / note |
|------|-----------------|
| Rust / Cargo | `/usr/local/cargo/bin` and `/usr/local/bin` (`cargo`, `rustc` on default `PATH`) |
| CLI (prebuilt) | `/usr/local/bin/bag-audit` — rebuild after fixing `bag-audit` crate sources |
| Workspace root | `/app` |
| Network | **Disabled** — do not run `apt-get`, `rustup`, or downloads; installs hang with no DNS |

Pre-flight:

```bash
which cargo rustc
export PATH="/usr/local/cargo/bin:$PATH"
```

## Rebuild

```bash
cd /app
cargo build --release --locked -p bag-audit
install -m 0755 target/release/bag-audit /usr/local/bin/bag-audit
bag-audit audit --bag /app/fixtures/bags/gap-monotonic --seed 7 --speed 1.0 \
  --export /app/output/gap-monotonic.sqlite
```

After editing `/app/crates/bag-audit/src/`, rebuild and reinstall so the verifier exercises your binary.
