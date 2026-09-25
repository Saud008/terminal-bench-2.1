# Frame index from simulation ticks

Simulation advances in ticks at `tick_rate` Hz. Animation samples run at `anim_fps` frames per second. Convert a tick to the animation frame used for pose sampling with round-half-up integer division:

```
frame = (tick * anim_fps + tick_rate / 2) / tick_rate
```

All integer arithmetic. The `tick_rate / 2` term is the half-tick bias before truncating toward zero.

Do not use `tick * anim_fps / tick_rate` without the bias; that truncates toward zero and misaligns hit windows at odd tick boundaries.

Every hit and replay event written to the ledger or collision report must carry the `frame` value computed with this formula for its tick.
