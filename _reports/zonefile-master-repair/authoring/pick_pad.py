"""Find TXT lengths whose zone digest input ends in the 112..119 byte zone of
the last SHA-384 block (build a variant with the 120-byte threshold)."""
import subprocess
import sys
from pathlib import Path

subprocess.run("rm -rf /tmp/v && cp -r /app /tmp/v && sed -i 's/buflen > 112/buflen > 120/' /tmp/v/src/sha384.c"
               " && make -s -C /tmp/v BUILD=/tmp/v/b", shell=True, check=True)
template = Path(sys.argv[1]).read_text()
hits = []
for n in range(1, 200):
    Path("/tmp/p.zone").write_text(template.replace("@PAD@", "x" * n))
    a = subprocess.run(["/app/build/zonec", "-o", "example.org", "/tmp/p.zone"], capture_output=True, text=True).stdout
    b = subprocess.run(["/tmp/v/b/zonec", "-o", "example.org", "/tmp/p.zone"], capture_output=True, text=True).stdout
    if a != b:
        hits.append(n)
print(hits)
