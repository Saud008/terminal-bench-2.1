# Manifest reachability

Reachability starts from the current snapshot manifest_list root.

Traverse manifest entries with status added or existing.

When nested_manifest is present, recursively traverse that manifest file before counting data_file paths.

Deleted status entries do not contribute live file references.
