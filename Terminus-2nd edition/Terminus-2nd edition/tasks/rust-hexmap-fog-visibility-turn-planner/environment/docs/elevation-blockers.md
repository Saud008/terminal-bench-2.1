# Elevation blockers

When casting LOS from an observer cell to a target cell, inspect every intermediate cell on the hex line (endpoints excluded).

An intermediate cell blocks LOS if and only if:

```
elev(intermediate) > min(elev(observer), elev(target))
```

Equal elevation does **not** block. Lower elevation never blocks. Endpoints never act as blockers for themselves.
