# Closure calendar contract

Terminal closure dates suspend yard operations. Closure days are excluded from dwell eligibility entirely.

## Exclusion semantics

A closure day does not count as eligible. It does not consume free time. It does not accrue demurrage tiers.

## Scenario source

Closure rows live in scenario JSON closures array with date YYYY-MM-DD and reason text.

## Interaction with holds

When a closure day overlaps a hold interval, closure exclusion removes the day from eligibility. Hold pause and closure exclusion both apply independently per calendar day.
