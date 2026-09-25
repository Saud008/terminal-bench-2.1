# Ignore patterns

Ignore patterns come from inventory root .inventory-ignore glob lines and ansible.cfg inventory ignore_patterns comma list.

Ignored paths must not contribute vars to effective host mappings.

Ignored files that contain plaintext secret keys still produce ignored_file_leak findings when scanned for repository hygiene.
