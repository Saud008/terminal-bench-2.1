# Fixture catalog

Batches under `/app/fixtures/batches/`:

| file | focus |
|------|-------|
| `001-gauge-basic.txt` | gauge types, multi-ds values |
| `002-derive-pair.txt` | derive rate from two epochs within skew window |
| `003-escaped-slash.txt` | quoted identifier with `\/` |
| `004-flush-boundary.txt` | readings on flush window edges |
| `005-skew-edge.txt` | anchor skew accept/reject boundary |
| `006-mixed-types.txt` | gauge + derive + counter in one batch |
| `007-counter-wrap.txt` | counter delta with uint32 wrap |
