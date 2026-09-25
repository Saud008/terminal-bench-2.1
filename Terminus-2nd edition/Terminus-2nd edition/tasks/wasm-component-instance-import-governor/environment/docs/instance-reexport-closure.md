# Instance re-export integrity closure

Integrity gate for surface export attestation: re-export edges map an outer surface name to an inner symbol on a via-instance id. Nested instance exports link instance names to child instance ids.

Surface resolution must walk re-export edges and nested instance links transitively until a terminal function export name is reached. Stopping after a single hop when further instance links or re-exports remain is incorrect.

Terminal function lookup is valid only on instance id 0. Function export names on non-zero instance ids are not admitted as resolved leaves; when following a nested instance link, the child instance id must be 0 for a terminal function to resolve. Looking up function leaves on any other instance id yields no terminal.

The resolved_leaf field in attestation records the terminal function export name.
