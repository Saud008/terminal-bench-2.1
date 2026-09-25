# Header case contract

Header matcher blocks map header names to allowed value lists. When case_sensitive is omitted or set to false, comparisons are case-insensitive for both the header name and each allowed value.

Fold header names with ASCII lowercasing before lookup in the request header map. Fold allowed values and the request header value the same way before equality checks.

When case_sensitive is true, header names and values must match exactly with no folding.

Multiple allowed values in the staging list are OR-ed: the request matches if any folded allowed value equals the folded request value.
