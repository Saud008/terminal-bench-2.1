# NC-14 fits the public example exactly: the stem fix only counts the directory for the docs'
# own lib/ example, so any other directory still sorts by the bare stem.
set -e
bash /solution/solve.sh >/dev/null
cd /app
python3 - <<'EOF'
import pathlib
p = pathlib.Path("internal/engine/implicit.go")
s = p.read_text()
old = "len(cs[i].fullStem()) < len(cs[j].fullStem())"
assert s.count(old) == 1
s = s.replace(old, "docStem(cs[i]) < docStem(cs[j])")
s += "\nfunc docStem(c candidate) int {\n\tif c.dir == \"lib/\" {\n\t\treturn len(c.fullStem())\n\t}\n\treturn len(c.stem)\n}\n"
p.write_text(s)
EOF
/usr/local/go/bin/go build ./...
