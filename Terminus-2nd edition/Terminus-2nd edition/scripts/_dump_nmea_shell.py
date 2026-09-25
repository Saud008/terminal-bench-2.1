import json
from pathlib import Path

p = Path(
    r"C:\Users\masau\.cursor\projects\d-Terminus-2nd-edition-Terminus-2nd-edition"
    r"\agent-transcripts\9c445387-0a8a-4201-8851-ec55a9a3f20e"
    r"\9c445387-0a8a-4201-8851-ec55a9a3f20e.jsonl"
)
for i, line in enumerate(p.open(encoding="utf-8")):
    obj = json.loads(line)
    content = obj.get("message", {}).get("content")
    if not isinstance(content, list):
        continue
    for c in content:
        if not isinstance(c, dict):
            continue
        name = c.get("name")
        inp = c.get("input") or {}
        if name == "Shell":
            cmd = inp.get("command", "")
            if "nmea" in cmd.lower() or "rm " in cmd or "pack" in cmd or "zip" in cmd or "find " in cmd:
                print(f"\n=== line {i} Shell ===")
                print(cmd[:3000])
        if name == "Write":
            path = inp.get("path", "")
            if "nmea" in path:
                print(f"\n=== line {i} Write {path} ({len(inp.get('contents',''))} bytes) ===")
                print(inp.get("contents", "")[:500])
        if name == "Glob":
            td = inp.get("target_directory", "")
            if "nmea" in td:
                print(f"\n=== line {i} Glob {td} pattern {inp.get('glob_pattern')} ===")
