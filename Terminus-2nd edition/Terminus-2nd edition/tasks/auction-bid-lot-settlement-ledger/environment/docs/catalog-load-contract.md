# catalog-load-contract

load-catalog clears prior SQLite rows in lots, bids, deposits, adjustments, and awards. scenario_id meta must match the --scenario flag. Bidstream rows land in the awards_buffer prerequisite tables before adjudicate-lots runs.
