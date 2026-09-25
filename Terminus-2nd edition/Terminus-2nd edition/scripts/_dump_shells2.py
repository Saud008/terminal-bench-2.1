import json
from pathlib import Path

p = Path(
    r"C:\Users\masau\.cursor\projects\d-Terminus-2nd-edition-Terminus-2nd-edition"
    r"\agent-transcripts\9c445387-0a8a-4201-8851-ec55a9a3f20e"
    r"\9c445387-0a8a-4201-8851-ec55a9a3f20e.jsonl"
)
for i, line in enumerate(p.open(encoding="utf-8")):
    if i < 29:
        continue
    obj = json.loads(line)
    content = obj.get("message", {}).get("content")
    if not isinstance(content, list):
        continue
    for c in content:
        if isinstance(c, dict) and c.get("name") == "Shell":
            cmd = c["input"].get("command", "")
            print(f"\n===== LINE {i} ({len(cmd)} chars) =====")
            print(cmd)
        if isinstance(c, dict) and c.get("name") == "Write" and i >= 55:
            path = c["input"].get("path", "")
            print(f"\n===== LINE {i} WRITE {path} =====")
            print(c["input"].get("contents", "")[:2000])
