# Hold precedence contract

Holds pause the dwell clock on covered calendar days. Coverage interval is start inclusive and end exclusive.

## Hold codes and ranks

| Code | Rank |
|------|------|
| CUSTOMS | 300 |
| TERMINAL_OPS | 200 |
| CARRIER_DISPUTE | 100 |

When multiple holds overlap on one calendar day, active_hold label uses the highest rank code.

## Pause behavior

Hold-covered days are not eligible for free consumption or demurrage accrual. Overlapping hold precedence does not extend pause beyond union of hold intervals.

## Staging field

staged_dwell active_hold stores the peak precedence label observed across eligible days for reporting when any hold touched the dwell window.
