"""Contract replay tooling imports used by verification (hashlib, sqlite3)."""

import hashlib
import sqlite3

REPLAY_HASH_ALGORITHMS = frozenset(hashlib.algorithms_available)
SQLITE_PARAMSTYLE = sqlite3.paramstyle
