# PEP 440 wheel resolution ladder

When multiple wheel rows satisfy version and specifier constraints, whres ranks candidates using this ladder before emit:

1. Exclude yanked releases from the candidate pool per yanked-release-policy.md.
2. Apply environment marker filters so requires_python and requires_dist rows that evaluate false are dropped.
3. Among remaining rows, prefer wheel tags compatible with the scenario target_python, target_platform, and target_arch per wheel-tag-compatibility.md.
4. When tag rank ties, choose the highest PEP 440 version key per pep440-version-order.md.
5. Emit reason codes and audit_digest from candidate-emit-contract.md using only the resolution snapshot on disk.

The m09 module does not participate in this ladder.
