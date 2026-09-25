# License file precedence

Resolve the effective SPDX license for a vendored crate directory using this order:

1. license-file path in Cargo.toml when the referenced file exists (first line is the SPDX token)
2. Otherwise the lexicographically first LICENSE* file in the crate root (first non-empty line)
3. Otherwise the lexicographically first COPYING* file using the same first-line rule
4. Otherwise the license field in Cargo.toml
5. Otherwise UNKNOWN

Normalize OR and AND connectors with single spaces. License drift is when resolved_license differs from lock-metadata declared_license for that name@version.
