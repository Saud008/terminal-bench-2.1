import hashlib
import os
import subprocess
import sys

bad = []
for n in range(0, 400):
    data = os.urandom(n)
    got = subprocess.run([sys.argv[1]], input=data, capture_output=True).stdout.decode().strip()
    if got != hashlib.sha384(data).hexdigest():
        bad.append(n)
print("mismatching lengths:", bad if bad else "none")
