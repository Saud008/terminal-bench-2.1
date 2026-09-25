# Cleaning reset window

When hour_index equals a cleaning_events hour_index inclusively, set p_base for that batch to pressure_bar at that hour before computing NDP. Cleaning reset applies at the cleaning hour row and all subsequent rows for that batch until another reset.
