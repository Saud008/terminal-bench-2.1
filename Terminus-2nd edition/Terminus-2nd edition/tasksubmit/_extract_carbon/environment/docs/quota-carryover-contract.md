# Quota carryover contract

Each region has quota_per_window and max_carryover. Available compute in window w equals base_quota plus carry_in. After scheduling, used cannot exceed available. carry_out equals min(max_carryover, available minus used) and becomes carry_in for window w+1. quota_ledger rows must appear sorted by region then window_index.
