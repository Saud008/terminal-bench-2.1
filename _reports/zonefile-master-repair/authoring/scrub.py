import pathlib
import re
import sys

slug = "zonefile-master-repair"
canon = f"/terminal-bench2.1/{slug}"
root = pathlib.Path(sys.argv[1])
rules = [
    (re.compile(r'"trial_uri": "file://[^"]*"'), f'"trial_uri": "file://{canon}"'),
    (re.compile(r'"(trials_dir|jobs_dir|path|task_dir)": "(/home/[^"]*|/mnt/[^"]*|/Users/[^"]*)"'),
     lambda m: f'"{m.group(1)}": "{canon}"'),
]
for f in list(root.rglob("config.json")) + list(root.rglob("result.json")):
    text = f.read_text(encoding="utf-8")
    new = text
    for pat, rep in rules:
        new = pat.sub(rep, new)
    if new != text:
        f.write_text(new, encoding="utf-8", newline="\n")
        print("scrubbed", f)
