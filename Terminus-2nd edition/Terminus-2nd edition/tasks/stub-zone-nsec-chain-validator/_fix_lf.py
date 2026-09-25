from pathlib import Path
root = Path(r"d:\Terminus-2nd edition\Terminus-2nd edition\tasks\stub-zone-nsec-chain-validator")
for rel in ["solution/solve.sh", "tests/test.sh"]:
    p = root / rel
    p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n"))
print("lf ok")
