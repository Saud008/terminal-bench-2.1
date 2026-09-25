# Verifier contract

Independent pytest helpers recompute staging digests and export rows using the same rules documented in /app/docs/staging-snapshot.md and /app/docs/export-plan-schema.md.

## Libraries

The verifier may import hashlib for SHA-256 digests and fnmatch for MODALIAS glob comparisons. Agents implement the same math in Bash with sha256sum and shell glob rules. /app/scripts/digest_math.py documents the same primitives.

## Verifier-only assets

The verifier may also load extra verifier-only fixture assets that are not bundled under /app/fixtures. Those assets stay on the test side and are not part of the agent-visible environment tree.

## CLI invocation

Pytest invokes /app/lib/cli.sh through bash. The /app/bin/udev-policy-planner entry point is a symlink to the same implementation.
