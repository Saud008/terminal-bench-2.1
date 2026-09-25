# Hex cube coordinates

Playfield cells use axial coordinates `(q, r)` with implied cube component `s = -q - r`.

Cube distance between two cells `(q0, r0)` and `(q1, r1)` is:

```
(|q1 - q0| + |r1 - r0| + |s1 - s0|) / 2
```

where `s0 = -q0 - r0` and `s1 = -q1 - r1`. Distance is always an integer for valid hex cells.

Vision radius checks and LOS ray length use this cube distance.
