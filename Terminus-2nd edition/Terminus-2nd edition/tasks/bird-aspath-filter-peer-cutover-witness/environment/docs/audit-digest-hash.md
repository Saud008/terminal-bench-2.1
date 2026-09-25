# Audit digest hash

The sealed report audit_digest is lowercase hex sha256. Verifier contract math may use Python hashlib.sha256 over the same UTF-8 line material. A small helper lives at /app/tools/audit_digest_ref.py for the same digest primitive.
