# Runway normalization lemma

Runway designators are canonicalized by trimming whitespace, uppercasing, then stripping leading zeros from the numeric prefix while preserving any trailing `L`, `R`, or `C` suffix.

Examples: `09L` and `9l` both canonicalize to `9L`; `27R` stays `27R`.

A `runway` kind NOTAM row closes a flight runway when the canonical designators are equal and the flight airport equals the NOTAM airport compared case-insensitively. A match contributes a `runway_closure` closure.
