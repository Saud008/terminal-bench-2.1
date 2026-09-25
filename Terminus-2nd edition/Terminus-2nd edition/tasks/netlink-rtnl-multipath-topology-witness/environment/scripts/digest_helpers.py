"""Digest and address helpers aligned with /app/docs/export-digest-schema.md."""

from __future__ import annotations

import hashlib
import ipaddress
import struct

_PRIMITIVES = (hashlib, ipaddress, struct)
