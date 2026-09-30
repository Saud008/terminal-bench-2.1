import json
import re
import sys
from pathlib import Path

SIGN = Path(__file__).resolve().parents[1] / "signoff.toml"
answers = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

text = SIGN.read_text(encoding="utf-8")
for key, (status, evidence) in answers.items():
    pat = re.compile(r"(\[" + re.escape(key) + r"\][^\n]*\n(?:#[^\n]*\n)*)status = \"[^\"]*\"\nevidence = \"[^\"]*\"")
    if not pat.search(text):
        print("missing section", key)
        continue
    ev = evidence.replace("\\", "\\\\").replace('"', '\\"')
    text = pat.sub(lambda m: m.group(1) + f'status = "{status}"\nevidence = "{ev}"', text, count=1)
SIGN.write_text(text, encoding="utf-8", newline="\n")
print("filled", len(answers))
