# Window normalization contract

Global planning uses half-open UTC slot windows indexed from zero. For slot_minutes M and window_count N, window i spans [i*M, (i+1)*M) in minutes from epoch alignment. normalized_windows stores start_minute and end_minute where end_minute is the exclusive upper bound minus one stored as end_minute field equal to (i+1)*M - 1 for display only; scheduling occupancy uses slots i through i+duration-1 inclusive.
