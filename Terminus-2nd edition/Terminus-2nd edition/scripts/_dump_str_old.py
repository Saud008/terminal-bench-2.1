import json
from pathlib import Path

p = Path(
    r"C:\Users\masau\.cursor\projects\d-Terminus-2nd-edition-Terminus-2nd-edition"
    r"\agent-transcripts\9c445387-0a8a-4201-8851-ec55a9a3f20e"
    r"\9c445387-0a8a-4201-8851-ec55a9a3f20e.jsonl"
)
out = Path(
    r"c:\Users\masau\Downloads\Terminus-2nd edition (1)\Terminus-2nd edition"
    r"\Terminus-2nd edition\scripts\_nmea_strreplace_dump"
)
out.mkdir(exist_ok=True)
n = 0
for i, line in enumerate(p.open(encoding="utf-8")):
    obj = json.loads(line)
    content = obj.get("message", {}).get("content")
    if not isinstance(content, list):
        continue
    for j, c in enumerate(content):
        if not isinstance(c, dict) or c.get("name") != "StrReplace":
            continue
        inp = c.get("input") or {}
        path = inp.get("path", "")
        if "nmea0183" not in path:
            continue
        rel = path.split("checksum-merge")[-1].strip("\\/")
        safe = rel.replace("\\", "_").replace("/", "_")
        old = inp.get("old_string", "")
        new = inp.get("new_string", "")
        (out / f"{i:02d}_{j}_{safe}.old.txt").write_text(old, encoding="utf-8")
        (out / f"{i:02d}_{j}_{safe}.new.txt").write_text(new, encoding="utf-8")
        n += 1
        print(f"{i}:{j} {rel} old={len(old)} new={len(new)}")
print("dumped", n)
