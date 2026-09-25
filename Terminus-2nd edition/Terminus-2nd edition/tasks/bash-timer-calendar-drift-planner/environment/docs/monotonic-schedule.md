# Monotonic schedule

OnBootSec and OnUnitActiveSec use monotonic microseconds from activation.json and boot_monotonic_usec from the plan context.

Next monotonic fire is the earliest candidate among:

- boot_monotonic_usec plus OnBootSec converted to microseconds
- unit_active_monotonic_usec plus OnUnitActiveSec converted to microseconds

Convert the chosen monotonic target to UTC by adding the delta from boot_monotonic_usec to reference_now.

Mixed timers take the earlier of calendar next fire and monotonic next fire.
