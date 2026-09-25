# Path normalization

All layer tar header names are normalized before staging, materialize, and export.

Rules:

1. Trim surrounding whitespace.
2. Ensure a single leading slash.
3. Apply POSIX path clean to resolve `.` and `..` segments.
4. Collapse duplicate slashes.
5. Remove trailing slashes except for the root path `/`.
6. Empty input becomes `/`.

The same normalized path string must be used for duplicate detection and manifest entries.
