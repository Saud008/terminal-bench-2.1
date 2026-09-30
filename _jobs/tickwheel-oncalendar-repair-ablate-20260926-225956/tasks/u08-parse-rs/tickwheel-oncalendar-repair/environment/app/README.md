# tickwheel

tickwheel evaluates systemd `OnCalendar=` expressions the same way
`systemd-analyze calendar` does, so timer schedules can be checked on hosts
that don't run systemd (build containers, CI runners, macOS laptops).

```
$ tickwheel calendar --base-time='2026-03-28 12:00:00 UTC' --iterations=3 'Mon..Fri 09:30 Europe/Berlin'
  Original form: Mon..Fri 09:30 Europe/Berlin
Normalized form: Mon..Fri *-*-* 09:30:00 Europe/Berlin
    Next elapse: Mon 2026-03-30 07:30:00 UTC
       Iter. #2: Tue 2026-03-31 07:30:00 UTC
       Iter. #3: Wed 2026-04-01 07:30:00 UTC
```

Build with `cargo build --release`; the binary ends up in
`target/release/tickwheel`. The crate (`Cargo.toml`) has no dependencies
outside the Rust standard library.

## Layout

| path | contents |
|---|---|
| `src/cli.rs` | argument handling and the report table |
| `src/spec/` | expression parser, normalization, validity rules, normalized form |
| `src/engine/` | next-elapse search (`next.rs`), field matching, bounds check |
| `src/civil/` | broken-down time and the wall-time to instant conversion |
| `src/zone/` | TZif reader and POSIX footer rules |
| `src/timestamp.rs` | base-time parsing and timestamp formatting |
| `docs/` | the specification: `cli.md`, `syntax.md`, `normalization.md`, `elapse.md`, `timezones.md` |
