package engine

import (
	"os"
	"sort"
	"strings"

	"brickmake/internal/db"
	"brickmake/internal/expand"
	"brickmake/internal/text"
)

// maxChain bounds implicit rule chains.
const maxChain = 16

// match is the result of implicit rule search for one target.
type match struct {
	rule      *db.PatternRule
	stem      string // $*, including the directory part
	normal    []string
	orderOnly []string
	also      []string // the rule's other targets
	inter     map[string]*match
}

type candidate struct {
	rule   *db.PatternRule
	target int
	dir    string // directory prepended to the stem, if any
	stem   string // the part matched by '%'
}

func (c candidate) fullStem() string { return c.dir + c.stem }

// candidates lists the pattern rules whose target pattern matches name,
// shortest stem first; rules of equal stem length keep makefile order. A
// target pattern without a slash is matched against the file part of a
// name that has a directory.
func (e *Engine) candidates(name string, used map[*db.PatternRule]bool) []candidate {
	dir, base := text.SplitDir(name)
	var cs []candidate
	for _, r := range e.db.PatternRules {
		if used[r] {
			continue
		}
		for ti, tp := range r.Targets {
			if tp == "%" {
				continue
			}
			var stem string
			var ok bool
			d := ""
			if dir == "" || strings.IndexByte(tp, '/') >= 0 {
				stem, ok = text.Match(tp, name)
			} else {
				stem, ok = text.Match(tp, base)
				d = dir
			}
			if !ok || stem == "" {
				continue
			}
			cs = append(cs, candidate{rule: r, target: ti, dir: d, stem: stem})
			break
		}
	}
	sort.SliceStable(cs, func(i, j int) bool {
		return len(cs[i].fullStem()) < len(cs[j].fullStem())
	})
	return cs
}

// prereqs computes a candidate's prerequisite names. For a directory-relative
// match, the directory is prepended only to prerequisites containing `%`.
func (e *Engine) prereqs(c candidate, name string, sc *expand.Scope) (normal, orderOnly []string) {
	pr := c.rule.Prereqs
	normal, orderOnly = pr.Normal, pr.OrderOnly
	if pr.Second {
		s := &expand.Scope{Auto: &expand.Auto{Target: name, Stem: c.fullStem()}}
		if sc != nil {
			s.Sets = sc.Sets
		}
		e.x.Pos = c.rule.Pos
		normal, orderOnly = text.SplitOrder(text.Fields(e.x.Expand(pr.Text, s)))
	}
	conv := func(words []string) []string {
		out := make([]string, len(words))
		for i, w := range words {
			out[i] = text.Subst(w, c.stem)
			if c.dir != "" && strings.IndexByte(w, '%') >= 0 {
				out[i] = c.dir + out[i]
			}
		}
		return out
	}
	return conv(normal), conv(orderOnly)
}

// oughtToExist reports whether a prerequisite exists or is a target in
// the makefile.
func (e *Engine) oughtToExist(name string) bool {
	if e.db.Lookup(name) != nil {
		return true
	}
	_, err := os.Stat(name)
	return err == nil
}

// findImplicit searches the pattern rules for name. The first pass accepts
// a rule whose prerequisites all exist or ought to exist; the second pass
// also accepts prerequisites that can be made by a chain of other pattern
// rules.
func (e *Engine) findImplicit(name string, sc *expand.Scope, depth int, used map[*db.PatternRule]bool) *match {
	type tried struct {
		c              candidate
		normal, orders []string
	}
	var ts []tried
	for _, c := range e.candidates(name, used) {
		n, o := e.prereqs(c, name, sc)
		ts = append(ts, tried{c, n, o})
	}
	all := func(t tried) []string { return append(append([]string{}, t.normal...), t.orders...) }
	for _, t := range ts {
		good := true
		for _, p := range all(t) {
			if !e.oughtToExist(p) {
				good = false
				break
			}
		}
		if good {
			return newMatch(t.c, t.normal, t.orders, nil)
		}
	}
	if depth >= maxChain {
		return nil
	}
	for _, t := range ts {
		inter := map[string]*match{}
		good := true
		for _, p := range all(t) {
			if e.oughtToExist(p) {
				continue
			}
			next := map[*db.PatternRule]bool{t.c.rule: true}
			for r := range used {
				next[r] = true
			}
			m := e.findImplicit(p, nil, depth+1, next)
			if m == nil {
				good = false
				break
			}
			inter[p] = m
		}
		if good {
			return newMatch(t.c, t.normal, t.orders, inter)
		}
	}
	return nil
}

func newMatch(c candidate, normal, orderOnly []string, inter map[string]*match) *match {
	m := &match{rule: c.rule, stem: c.fullStem(), normal: normal, orderOnly: orderOnly, inter: inter}
	for i, tp := range c.rule.Targets {
		if i != c.target {
			m.also = append(m.also, c.dir+text.Subst(tp, c.stem))
		}
	}
	return m
}

// implicitFor runs implicit rule search once for a file without a recipe.
func (e *Engine) implicitFor(n *node) {
	if n.searched {
		return
	}
	n.searched = true
	if r := n.f.RecipeRule(); r != nil {
		n.recipe = r.Recipe
		if r.Static {
			n.stem = r.Stem
		}
		return
	}
	if n.f.Phony {
		return
	}
	m := n.preset
	if m == nil {
		m = e.findImplicit(n.name(), e.scope(n), 0, map[*db.PatternRule]bool{})
	}
	if m == nil {
		return
	}
	n.match = m
	n.recipe = m.rule.Recipe
	n.stem = m.stem
	for _, p := range append(append([]string{}, m.normal...), m.orderOnly...) {
		created := e.db.Lookup(p) == nil
		pn := e.node(e.db.Enter(p))
		if sub := m.inter[p]; sub != nil && created {
			pn.intermediate = true
			pn.preset = sub
		}
	}
}
