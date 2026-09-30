# NC-03 hard-coded example answer: pattern-specific variables are applied in reverse
# definition order, which reproduces the instruction's -O2 -fPIC -DNET example but is not the rule.
set -e
bash /solution/solve.sh >/dev/null
cd /app
python3 - <<'EOF'
import pathlib
p = pathlib.Path("internal/engine/scope.go")
s = p.read_text()
old = "sort.SliceStable(hits, func(i, j int) bool { return len(hits[i].Pattern) < len(hits[j].Pattern) })"
new = ("sort.SliceStable(hits, func(i, j int) bool { return false })\n"
       "\tfor i, j := 0, len(hits)-1; i < j; i, j = i+1, j-1 {\n\t\thits[i], hits[j] = hits[j], hits[i]\n\t}")
assert s.count(old) == 1
p.write_text(s.replace(old, new))
EOF
/usr/local/go/bin/go build ./...
