# Access window contract

planned_minute = reported_minute + travel_buffer_minutes from meta.

Building access windows use inclusive end_minute: planned_minute must satisfy start_minute <= planned_minute <= end_minute.

Technician shift bounds are also inclusive on both ends.
