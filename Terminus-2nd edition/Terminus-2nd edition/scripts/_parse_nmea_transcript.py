import json
from pathlib import Path

p = Path(
    r"C:\Users\masau\.cursor\projects\d-Terminus-2nd-edition-Terminus-2nd-edition"
    r"\agent-transcripts\9c445387-0a8a-4201-8851-ec55a9a3f20e"
    r"\9c445387-0a8a-4201-8851-ec55a9a3f20e.jsonl"
)
for i, line in enumerate(p.open(encoding="utf-8")):
    obj = json.loads(line)
    role = obj.get("role")
    content = obj.get("message", {}).get("content")
    if isinstance(content, list):
        types = [c.get("type") if isinstance(c, dict) else type(c).__name__ for c in content]
        names = [c.get("name") for c in content if isinstance(c, dict) and c.get("name")]
        print(i, role, types[:10], names[:8])
    else:
        print(i, role, type(content).__name__, str(content)[:100] if content else None)
