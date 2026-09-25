import json
from pathlib import Path
from collections import defaultdict

roots = [
    Path(r"C:\Users\masau\.cursor\projects\d-Terminus-2nd-edition-Terminus-2nd-edition\agent-transcripts"),
    Path(r"C:\Users\masau\.cursor\projects\c-Users-masau-Downloads-Terminus-2nd-edition-1\agent-transcripts"),
]

writes = []
for root in roots:
    if not root.exists():
        continue
    for p in root.rglob("*.jsonl"):
        for line in p.open(encoding="utf-8", errors="ignore"):
            if "nmea0183-multipart" not in line:
                continue
            if '"Write"' not in line and '"StrReplace"' not in line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            content = obj.get("message", {}).get("content")
            if not isinstance(content, list):
                continue
            for c in content:
                if not isinstance(c, dict):
                    continue
                name = c.get("name")
                inp = c.get("input") or {}
                path = inp.get("path", "")
                if "nmea0183-multipart" not in path:
                    continue
                if name == "Write":
                    contents = inp.get("contents", "")
                    writes.append((p.parent.name, path, len(contents), contents))
                elif name == "StrReplace":
                    old = inp.get("old_string", "")
                    new = inp.get("new_string", "")
                    writes.append((p.parent.name, f"STRREPLACE:{path}", len(new), new[:200]))

print(f"total write/strreplace ops: {len(writes)}")
by_path = defaultdict(list)
for tid, path, n, contents in writes:
    rel = path.split("nmea0183-multipart-talker-checksum-merge")[-1]
    by_path[rel].append((tid, n, contents))

print("\nUnique relative paths:")
for rel in sorted(by_path):
    versions = by_path[rel]
    print(f"  {rel}: {len(versions)} ops, sizes={[v[1] for v in versions]}")

# Dump largest unique files from latest write
out = Path(r"c:\Users\masau\Downloads\Terminus-2nd edition (1)\Terminus-2nd edition\Terminus-2nd edition\scripts\_nmea_recovered")
out.mkdir(exist_ok=True)
recovered = 0
for rel, versions in by_path.items():
    if rel.startswith("STRREPLACE:"):
        continue
    # take largest write
    best = max(versions, key=lambda v: v[1])
    if best[1] < 20:
        continue
    target = out / rel.lstrip("\\/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(best[2], encoding="utf-8")
    recovered += 1
    print(f"recovered {rel} ({best[1]} bytes) from {best[0]}")
print(f"recovered files: {recovered}")
