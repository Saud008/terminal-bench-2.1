# Histogram merge

Histogram rollup merges bucket counts per le label within each window.

When bucket upper bounds shift between scrapes, retain the +Inf bucket count from the merge. Do not drop +Inf when le bounds change.

Merge uses scrape_order ascending within the window.
