"""Expose verifier-side derivation primitives without shipping answer helpers.

The task contract already defines a SHA-256 stream fingerprint and an
exponential half-life attenuation curve in docs. The verifier's independent
reference implementation uses Python's standard-library primitives for those
derivations, but the exact math lives in tests rather than the task env.
"""

import hashlib
import math

__all__ = ["hashlib", "math"]
