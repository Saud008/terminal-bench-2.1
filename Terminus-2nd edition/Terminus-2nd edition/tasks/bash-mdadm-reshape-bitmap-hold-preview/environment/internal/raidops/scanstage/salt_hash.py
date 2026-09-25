"""SHA-256 helpers for salted array names (hashlib)."""
import hashlib


def salted_name(host_salt: str, name: str) -> str:
    return hashlib.sha256(f"{host_salt}:{name}".encode()).hexdigest()[:16]
