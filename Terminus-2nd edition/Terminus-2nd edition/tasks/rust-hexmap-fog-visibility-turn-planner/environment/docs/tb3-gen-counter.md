# Turn clock contract

`fog_generation` lives on the board roster and fog mask.

- `load-board` initializes `fog_generation` to `0`.
- Each successful `reveal-fog` increments `fog_generation` by exactly `1`.
- Other subcommands do not advance the turn clock.
