# Bleed timing

Bleed ticks at **start of turn** before stun checks and before the act step.

When `bleed > 0`:

- Damage equals current bleed value.
- Subtract damage from hp (minimum 0).
- Decrement bleed by 1 (minimum 0).
- Emit `bleed` event with `damage`, `hp_after`, `bleed_after`.

If bleed is 0, no bleed event is emitted.

Bleed does not run at end of turn.
