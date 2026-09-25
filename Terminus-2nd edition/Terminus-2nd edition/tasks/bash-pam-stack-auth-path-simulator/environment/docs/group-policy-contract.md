# Group membership closure

subjects.json contains users with direct group lists and groups mapping group names to member names or nested group names.

Effective membership for a subject is the transitive closure built as follows:

1. Seed the effective set with the subject's direct groups **and the subject's own username**.
2. Expand each direct group through `groups` entries (nested group names that also appear as keys expand recursively to their members; leaf names are usernames).
3. Repeatedly add any group whose member list intersects the effective set (reverse / parent closure) until a fixed point.
4. Emit `subject_groups` as that effective set sorted lexicographically (usernames and group names both appear when present in the closure).

The username seed is required even when no group lists the subject by name: parent groups reached only through nested group keys still participate, and the subject name itself must appear in `subject_groups` when seeded.
