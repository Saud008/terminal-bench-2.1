# FilterSubject token rules

FilterSubject patterns use dot-separated tokens. A single asterisk token matches exactly one subject segment.

Example: orders.* matches orders.west but not orders.us.east.

The greater-than token is not used in bundled journals. Empty filter accepts all subjects on deliver.

Deliver skips messages whose subject fails filter matching.
