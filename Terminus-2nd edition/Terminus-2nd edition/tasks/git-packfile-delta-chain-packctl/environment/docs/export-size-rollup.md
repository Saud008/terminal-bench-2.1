# Export size rollup

total_inflated_bytes is the sum of inflated_size across all exported objects after full chain resolution.

Summing intermediate delta compressed_size values from staging, or mixing compressed and inflated lengths, is incorrect. Only final inflated payload lengths count toward the rollup.
