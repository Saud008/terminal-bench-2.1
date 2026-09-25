# Blackout window contract

Blackout windows block inspection scheduling when requested_day falls inside the window.

start_day is inclusive. end_day is the first schedulable day after the blackout span.

filter-blackouts writes eligible-dates.json listing permit_id keys that remain schedulable.