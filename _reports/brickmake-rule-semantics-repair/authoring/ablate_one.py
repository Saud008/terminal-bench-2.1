"""Inside the agent container after solve.sh: revert exactly one fix (argv[1])."""

import pathlib
import sys

REVERTS = {
    "stem": ("internal/engine/implicit.go",
             "len(cs[i].fullStem()) < len(cs[j].fullStem())",
             "len(cs[i].stem) < len(cs[j].stem)"),
    "dirs": ("internal/engine/implicit.go",
             "\t\t\tif strings.IndexByte(w, '%') < 0 {\n\t\t\t\tout[i] = w\n\t\t\t} else {\n\t\t\t\tout[i] = c.dir + text.Subst(w, c.stem)\n\t\t\t}\n",
             "\t\t\t_ = strings.IndexByte\n\t\t\tout[i] = c.dir + text.Subst(w, c.stem)\n"),
    "mention": ("internal/engine/implicit.go",
                "if e.db.Lookup(name) != nil {",
                "if f := e.db.Lookup(name); f != nil && (len(f.Rules) > 0 || f.Phony) {"),
    "patvars": ("internal/engine/scope.go",
                "return len(hits[i].Pattern) < len(hits[j].Pattern)",
                "return false"),
}

path, old, new = REVERTS[sys.argv[1]]
p = pathlib.Path("/app") / path
s = p.read_text()
assert s.count(old) == 1, f"{sys.argv[1]}: anchor not found once"
p.write_text(s.replace(old, new))
