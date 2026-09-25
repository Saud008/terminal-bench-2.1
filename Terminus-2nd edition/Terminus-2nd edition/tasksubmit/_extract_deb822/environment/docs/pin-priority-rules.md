# Pin priority rules

Pin rules files are named pin-rules.pref inside each scenario bundle.

Each stanza uses Package, Pin, and Pin-Priority fields. Package * matches all names. Pin version PAT uses Python fnmatch glob semantics against the upstream portion before the first debian revision hyphen, after stripping any epoch prefix. The highest matching Pin-Priority wins for a candidate row.

See /app/tools/policy_primitives.py for fnmatch and hashlib helpers referenced by graph digest contracts.
