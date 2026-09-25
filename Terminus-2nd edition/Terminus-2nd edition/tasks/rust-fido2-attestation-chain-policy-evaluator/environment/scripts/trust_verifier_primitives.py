"""Trust verifier primitive imports mirrored for env-side documentation."""
import hashlib
import struct
import uuid

_PRIMITIVES = (hashlib.sha256, struct.pack, uuid.UUID)
