package engine

import (
	"brickmake/internal/db"
	"brickmake/internal/expand"
	"brickmake/internal/text"
	"brickmake/internal/vars"
	"sort"
)

// patternSet collects the pattern-specific variables whose pattern matches
// the file into one set. Less-specific (shorter) patterns are applied first;
// patterns of equal length retain makefile order.
func (e *Engine) patternSet(n *node) *vars.Set {
	if n.patReady {
		return n.patVars
	}
	n.patReady = true
	var hits []*db.PatternVar
	for _, pv := range e.db.PatternVars {
		if _, ok := text.Match(pv.Pattern, n.name()); ok {
			hits = append(hits, pv)
		}
	}
	if len(hits) == 0 {
		return nil
	}
	sort.SliceStable(hits, func(i, j int) bool {
		return len(hits[i].Pattern) < len(hits[j].Pattern)
	})
	set := vars.NewSet()
	for _, pv := range hits {
		e.x.Pos = pv.Pos
		e.x.DefinePattern(set, pv.Name, pv.Op, pv.Value, pv.Pos)
	}
	n.patVars = set
	return set
}

// scope is the variable context of a file: its own target-specific
// variables, then its pattern-specific variables, then the context of the
// target that first asked for it, and finally the global variables.
func (e *Engine) scope(n *node) *expand.Scope {
	sc := &expand.Scope{}
	for x := n; x != nil; x = x.parent {
		sc.Sets = append(sc.Sets, x.f.Vars)
		if ps := e.patternSet(x); ps != nil {
			sc.Sets = append(sc.Sets, ps)
		}
	}
	return sc
}
