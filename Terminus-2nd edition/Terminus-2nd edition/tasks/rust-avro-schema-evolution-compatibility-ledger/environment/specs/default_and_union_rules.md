# Default values and union branch rules

## Reader defaults for missing writer fields

When the reader declares a field absent from the writer, compatibility requires a reader default **and** a promotion-safe type relationship for overlapping fields.

Allowed promotions include int to long and float to double. String to int is never allowed.

## Union branches

Union compatibility is **order-insensitive** at the branch-set level: writer branches ["null","string"] match reader ["string","null"].

Compare branch labels derived from primitive names or complex type names. Order must not break compatibility when the branch sets are identical.
