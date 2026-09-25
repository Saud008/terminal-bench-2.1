# Tolerance decision matrix

## Asymmetric bands

Each reading channel carries nominal, tol_plus, and tol_minus.

A channel is within_tolerance when:

value <= nominal + tol_plus AND value >= nominal - tol_minus

Do not collapse tol_plus and tol_minus into a single symmetric magnitude.

## Deviation field

deviation is abs(value - nominal) for reporting only. within_tolerance still follows the asymmetric band rules above.

## Out-of-tolerance count

out_of_tolerance_count counts channels where within_tolerance is false.
