# Quota window carryover

Each quota window has max_m3 and max_carry_m3. Available cubic meters equals max_m3 plus carry_in_m3. used_m3 sums assignment liters divided by 1000. carry_out_m3 equals min of max_carry_m3 and available minus used. carry_out becomes carry_in for the next window index.
