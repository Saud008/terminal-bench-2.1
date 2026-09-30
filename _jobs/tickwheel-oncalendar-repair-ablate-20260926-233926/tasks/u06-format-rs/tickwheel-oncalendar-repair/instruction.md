We check our systemd timer schedules in CI with tickwheel (source in `/app`) instead of booting systemd, and lately it keeps disagreeing with what the servers actually do. What people have run into so far:

- an `Europe/Dublin` timer checked across the last weekend of March prints the same elapse time on every row
- schedules on Lord Howe Island and in Havana come out wrong around the day their clocks go forward
- `Fri..Mon 18:00` gets accepted and scheduled, systemd refuses it
- the normalized form of two-day weekday lists like `Sat,Sun` isn't what systemd prints

That's probably not everything. tickwheel is supposed to print exactly what `systemd-analyze calendar` from systemd 252 (Debian bookworm, 252.39) prints under `TZ=UTC`, apart from the differences listed at the end of `/app/docs/cli.md`: same rows, same timestamps, same errors and exit codes. The docs in `/app/docs` are the spec, so make tickwheel follow them. It'll be checked with other expressions, zones and dates than the ones above.

Keep it plain Rust on the standard library only (no crates, no `unsafe` or FFI, no running other programs), keep the command line from `/app/docs/cli.md`, and a plain `cargo build --release` in `/app` has to keep working.
