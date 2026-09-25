# Tick index export schema

Written by `demo-index build` to the path given by `--out`.

```json
{
  "index_version": 1,
  "seed": "<seed string>",
  "files": ["<relative/path.dem>", "..."],
  "ticks": [
    {
      "global_tick": 0,
      "source": "alpha/late.dem",
      "usercmds": [
        {
          "seq": 1,
          "str_idx": 200,
          "string": "use_item",
          "arg": 42
        }
      ]
    }
  ],
  "stats": {
    "file_count": 0,
    "tick_count": 0,
    "usercmd_count": 0,
    "signon_resets": 0
  }
}
```

- `files` lists merge order (relative paths under `--root`).
- `ticks` is sorted ascending by `(global_tick, source)` where `source` uses normalized relative path byte order (see `demo-format.md`).
- `usercmds` contains only USERCMD packets for that tick row, sorted by `seq` ascending.
- `arg` is `raw_arg XOR mask`. Derive `mask` from the seed string and file `source` path:
  1. `digest =` lowercase hex SHA-256 of `seed + ":" + source + ":arg"` (64 characters).
  2. `mask = int(digest[0:8], 16)` — the first eight hex characters are the most-significant four bytes of the hash (not the trailing digest bytes).
- `stats.signon_resets` counts every SIGNON_RESET packet decoded across all files, including packets that appear mid-tick inside a tick index row.
