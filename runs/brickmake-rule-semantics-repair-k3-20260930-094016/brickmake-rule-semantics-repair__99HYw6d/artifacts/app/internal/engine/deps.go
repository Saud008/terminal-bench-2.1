package engine

import (
	"brickmake/internal/db"
	"brickmake/internal/expand"
	"brickmake/internal/text"
)

// ruleWords returns the prerequisites of one explicit rule, performing
// secondary expansion when the rule was read after .SECONDEXPANSION.
func (e *Engine) ruleWords(n *node, r *db.Rule) (normal, orderOnly []string) {
	if !r.Second {
		return r.Normal, r.OrderOnly
	}
	sc := e.scope(n)
	sc.Auto = &expand.Auto{Target: n.name(), Stem: r.Stem}
	e.x.Pos = r.Pos
	normal, orderOnly = text.SplitOrder(text.Fields(e.x.Expand(r.Text, sc)))
	if r.Static {
		for i, w := range normal {
			normal[i] = text.Subst(w, r.Stem)
		}
		for i, w := range orderOnly {
			orderOnly[i] = text.Subst(w, r.Stem)
		}
	}
	return normal, orderOnly
}

// depsOf returns the file's prerequisites in the order make considers
// them: those of the implicit rule, then those of the rule that supplies
// the recipe, then those of the other rules in makefile order.
func (e *Engine) depsOf(n *node) []dep {
	if n.depsReady {
		return n.deps
	}
	n.depsReady = true
	type list struct{ normal, orderOnly []string }
	var lists []list
	if m := n.match; m != nil {
		lists = append(lists, list{m.normal, m.orderOnly})
	}
	rr := n.f.RecipeRule()
	if rr != nil {
		nw, ow := e.ruleWords(n, rr)
		lists = append(lists, list{nw, ow})
	}
	for _, r := range n.f.Rules {
		if r != rr {
			nw, ow := e.ruleWords(n, r)
			lists = append(lists, list{nw, ow})
		}
	}
	normal := map[string]bool{}
	for _, l := range lists {
		for _, w := range l.normal {
			normal[w] = true
		}
	}
	for _, l := range lists {
		for _, w := range l.normal {
			n.deps = append(n.deps, dep{n: e.node(e.db.Enter(w))})
		}
		for _, w := range l.orderOnly {
			if !normal[w] {
				n.deps = append(n.deps, dep{n: e.node(e.db.Enter(w)), order: true})
			}
		}
	}
	return n.deps
}

// autoVars computes the automatic variables of a recipe.
func (e *Engine) autoVars(n *node) *expand.Auto {
	a := &expand.Auto{Target: n.name(), Stem: n.stem}
	var order []string
	for _, d := range e.depsOf(n) {
		if d.order {
			order = append(order, d.n.name())
			continue
		}
		a.Plus = append(a.Plus, d.n.name())
	}
	a.All = text.Uniq(a.Plus)
	a.Order = text.Uniq(order)
	if len(a.Plus) > 0 {
		a.First = a.Plus[0]
	}
	for _, name := range a.All {
		d := e.node(e.db.Lookup(name))
		if !n.st.exists || d.f.Phony || e.outdated(d, n) {
			a.Newer = append(a.Newer, name)
		}
	}
	return a
}
