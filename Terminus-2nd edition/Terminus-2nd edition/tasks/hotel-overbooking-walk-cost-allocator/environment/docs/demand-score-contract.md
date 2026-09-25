# Finance demand score formula

demand_score equals float(1000 minus arrival_rank) multiplied by (1.0 minus cancel_prob) plus protection_rank times 0.01 where protection_rank comes from loyalty tier lookup with default 50.
