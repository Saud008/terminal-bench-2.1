#!/usr/bin/env bash
set -euo pipefail

cd /app

cat > internal/engine/implicit.go <<'IMPLICIT_GO'
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
// name that has a directory, and the directory becomes part of the stem.
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

// prereqs computes a candidate's prerequisite names. The directory of a
// directory-relative match is prepended to every prerequisite that
// contains '%'.
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
			if strings.IndexByte(w, '%') < 0 {
				out[i] = w
			} else {
				out[i] = c.dir + text.Subst(w, c.stem)
			}
		}
		return out
	}
	return conv(normal), conv(orderOnly)
}

// oughtToExist reports whether a prerequisite exists or is mentioned in
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
IMPLICIT_GO

cat > internal/engine/scope.go <<'SCOPE_GO'
package engine

import (
	"sort"

	"brickmake/internal/db"
	"brickmake/internal/expand"
	"brickmake/internal/text"
	"brickmake/internal/vars"
)

// patternSet collects the pattern-specific variables whose pattern matches
// the file into one set. Definitions are applied from the shortest pattern
// to the longest (definitions of equal length in makefile order), so the
// most specific pattern is applied last.
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
	sort.SliceStable(hits, func(i, j int) bool { return len(hits[i].Pattern) < len(hits[j].Pattern) })
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
SCOPE_GO

cat > internal/engine/update.go <<'UPDATE_GO'
package engine

import (
	"fmt"

	"brickmake/internal/diag"
)

// outdated reports whether prerequisite d makes target n out of date. A
// prerequisite that is phony, missing, or remade in a dry run always does.
func (e *Engine) outdated(d, n *node) bool {
	if d.f.Phony || d.st.newest || !d.st.exists {
		return true
	}
	return !n.st.exists || d.st.t.After(n.st.t)
}

func (e *Engine) noRule(n, parent *node) {
	msg := fmt.Sprintf("No rule to make target '%s'", n.name())
	if parent != nil {
		msg += fmt.Sprintf(", needed by '%s'", parent.name())
	}
	if e.KeepGoing {
		diag.Err("*** %s.", msg)
	} else {
		diag.Err("*** %s.  Stop.", msg)
	}
}

func (e *Engine) fail(n, parent *node, depFailure bool) status {
	n.state, n.status = done, failed
	if depFailure && parent == nil && e.KeepGoing && !e.DryRun {
		diag.Err("Target '%s' not remade because of errors.", n.name())
	}
	return failed
}

// update brings n up to date on behalf of parent (nil for a goal).
func (e *Engine) update(n, parent *node) status {
	switch n.state {
	case done:
		return n.status
	case running:
		diag.Err("Circular %s <- %s dependency dropped.", parent.name(), n.name())
		return dropped
	}
	n.state = running
	if n.parent == nil {
		n.parent = parent
	}
	e.implicitFor(n)
	deps := e.depsOf(n)
	n.stat()
	if !n.hasRule() && !n.st.exists {
		e.noRule(n, parent)
		return e.fail(n, parent, false)
	}

	must, bad := false, false
	for _, d := range deps {
		var st status
		if d.n.intermediate && d.n.state != done {
			hit := false
			st = e.checkIntermediate(d.n, n, &hit)
			if hit && !d.order {
				must = true
			}
		} else {
			st = e.update(d.n, n)
			if st == ok && !d.order && e.outdated(d.n, n) {
				must = true
			}
		}
		if st == failed {
			bad = true
			if !e.KeepGoing {
				break
			}
		}
	}
	if bad {
		return e.fail(n, parent, true)
	}
	if n.f.Phony || !n.st.exists || e.AlwaysMake {
		must = true
	}
	if !must {
		n.state, n.status = done, ok
		return ok
	}
	for _, d := range deps {
		if d.n.intermediate && d.n.state != done {
			if e.update(d.n, n) == failed {
				bad = true
				if !e.KeepGoing {
					break
				}
			}
		}
	}
	if bad {
		return e.fail(n, parent, true)
	}
	return e.remake(n)
}

// checkIntermediate decides whether a missing intermediate file matters to
// target: it does when the intermediate exists and is newer than target,
// or when anything it depends on is. The intermediate itself is only made
// later, if target has to be remade.
func (e *Engine) checkIntermediate(m, target *node, hit *bool) status {
	if m.parent == nil {
		m.parent = target
	}
	e.implicitFor(m)
	m.stat()
	if m.st.exists && (!target.st.exists || m.st.t.After(target.st.t)) {
		*hit = true
		return ok
	}
	if !m.hasRule() {
		return ok
	}
	for _, d := range e.depsOf(m) {
		var st status
		if d.n.intermediate && d.n.state != done {
			sub := false
			st = e.checkIntermediate(d.n, target, &sub)
			if sub && !d.order {
				*hit = true
			}
		} else {
			st = e.update(d.n, m)
			if st == ok && !d.order && e.outdated(d.n, target) {
				*hit = true
			}
		}
		if st == failed && !e.KeepGoing {
			return failed
		}
	}
	return ok
}

// remake runs n's recipe, or records that a target without a recipe was
// "remade" by doing nothing.
func (e *Engine) remake(n *node) status {
	if n.recipe == nil {
		n.state, n.status = done, ok
		n.stat()
		return ok
	}
	auto := e.autoVars(n)
	n.started = true
	good := e.run(n, auto)
	n.state = done
	if !good {
		n.status = failed
		return failed
	}
	n.status = ok
	e.refresh(n)
	if n.match != nil {
		for _, name := range n.match.also {
			o := e.node(e.db.Enter(name))
			if o.state != done {
				o.state, o.status, o.started = done, ok, true
				o.intermediate = o.intermediate || n.intermediate
				e.refresh(o)
			}
		}
	}
	return ok
}

// refresh re-reads a remade target's time. In a dry run the target counts
// as newer than everything.
func (e *Engine) refresh(n *node) {
	if e.DryRun && !allForced(n.recipe) {
		n.st = stamp{newest: true}
		return
	}
	n.stat()
}
UPDATE_GO

cat > internal/engine/engine.go <<'ENGINE_GO'
// Package engine decides which targets are out of date and runs their
// recipes.
package engine

import (
	"fmt"
	"os"

	"brickmake/internal/db"
	"brickmake/internal/diag"
	"brickmake/internal/expand"
)

// Engine updates goals against a rule database.
type Engine struct {
	DryRun     bool
	Silent     bool
	KeepGoing  bool
	AlwaysMake bool
	Shell      string
	Env        []string

	db      *db.DB
	x       *expand.Expander
	nodes   map[*db.File]*node
	order   []*node
	started int
}

func New(d *db.DB, x *expand.Expander) *Engine {
	return &Engine{db: d, x: x, nodes: map[*db.File]*node{}, Shell: "/bin/sh"}
}

func (e *Engine) node(f *db.File) *node {
	if n := e.nodes[f]; n != nil {
		return n
	}
	n := &node{f: f}
	e.nodes[f] = n
	e.order = append(e.order, n)
	return n
}

// Run updates the goals in order and returns the exit status.
func (e *Engine) Run(goals []string) (code int) {
	defer e.removeIntermediates()
	defer func() {
		if r := recover(); r != nil {
			f, isFatal := r.(diag.Fatal)
			if !isFatal {
				panic(r)
			}
			fmt.Fprintln(diag.Stderr, f.Error())
			code = 2
		}
	}()
	anyFailed := false
	for _, g := range goals {
		n := e.node(e.db.Enter(g))
		before := e.started
		if e.update(n, nil) == failed {
			anyFailed = true
			if !e.KeepGoing {
				break
			}
			continue
		}
		if e.started == before {
			if n.f.Phony || n.recipe == nil {
				diag.Say("Nothing to be done for '%s'.", g)
			} else {
				diag.Say("'%s' is up to date.", g)
			}
		}
	}
	if anyFailed {
		return 2
	}
	return 0
}

// removeIntermediates deletes the intermediate files made by this run.
func (e *Engine) removeIntermediates() {
	first := true
	for _, n := range e.order {
		if !n.intermediate || !n.started || n.f.Precious || e.db.SecondaryAll {
			continue
		}
		if !e.DryRun {
			if err := os.Remove(n.name()); err != nil && os.IsNotExist(err) {
				continue
			}
		}
		if e.Silent {
			continue
		}
		if first {
			fmt.Fprint(diag.Stdout, "rm ")
			first = false
		} else {
			fmt.Fprint(diag.Stdout, " ")
		}
		fmt.Fprint(diag.Stdout, n.name())
	}
	if !first {
		fmt.Fprintln(diag.Stdout)
	}
}
ENGINE_GO

cat > internal/engine/deps.go <<'DEPS_GO'
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
DEPS_GO

cat > internal/expand/define.go <<'DEFINE_GO'
package expand

import (
	"brickmake/internal/diag"
	"brickmake/internal/vars"
)

// DefineGlobal applies an assignment to the global set. Makefile
// assignments never replace a command-line variable.
func (e *Expander) DefineGlobal(name string, op vars.Op, value string, origin vars.Origin, pos diag.Pos) {
	g := e.Global
	old := g.Get(name)
	if old != nil && old.Origin == vars.CommandLine && origin != vars.CommandLine {
		return
	}
	switch op {
	case vars.OpRecursive:
		g.Put(&vars.Var{Name: name, Value: value, Flavor: vars.Recursive, Origin: origin, Pos: pos})
	case vars.OpSimple:
		g.Put(&vars.Var{Name: name, Value: e.Expand(value, nil), Flavor: vars.Simple, Origin: origin, Pos: pos})
	case vars.OpConditional:
		if old == nil {
			g.Put(&vars.Var{Name: name, Value: value, Flavor: vars.Recursive, Origin: origin, Pos: pos})
		}
	case vars.OpAppend:
		if old == nil {
			g.Put(&vars.Var{Name: name, Value: value, Flavor: vars.Recursive, Origin: origin, Pos: pos})
			return
		}
		add := value
		if old.Flavor == vars.Simple {
			add = e.Expand(value, nil)
		}
		g.Put(&vars.Var{Name: name, Value: vars.Paste(old.Value, add), Flavor: old.Flavor, Origin: origin, Pos: pos})
	}
}

// DefineIn applies a target- or pattern-specific assignment to set. The
// enclosing scope used for ":=" and "?=" is set followed by the global set.
func (e *Expander) DefineIn(set *vars.Set, name string, op vars.Op, value string, pos diag.Pos) {
	if g := e.Global.Get(name); g != nil && g.Origin == vars.CommandLine {
		set.Put(&vars.Var{Name: name, Value: g.Value, Flavor: g.Flavor, Origin: vars.CommandLine, Pos: g.Pos})
		return
	}
	e.defineIn(set, name, op, value, pos)
}

// DefinePattern applies one pattern-specific assignment while building a
// file's pattern set. A command-line variable replaces the assigned text
// but the operator is kept.
func (e *Expander) DefinePattern(set *vars.Set, name string, op vars.Op, value string, pos diag.Pos) {
	if g := e.Global.Get(name); g != nil && g.Origin == vars.CommandLine {
		value = g.Value
	}
	if op == vars.OpSimple {
		set.Put(&vars.Var{Name: name, Value: value, Flavor: vars.Simple, Origin: vars.File, Pos: pos})
		return
	}
	e.defineIn(set, name, op, value, pos)
}

func (e *Expander) defineIn(set *vars.Set, name string, op vars.Op, value string, pos diag.Pos) {
	sc := &Scope{Sets: []*vars.Set{set}}
	switch op {
	case vars.OpRecursive:
		set.Put(&vars.Var{Name: name, Value: value, Flavor: vars.Recursive, Origin: vars.File, Pos: pos})
	case vars.OpSimple:
		set.Put(&vars.Var{Name: name, Value: e.Expand(value, sc), Flavor: vars.Simple, Origin: vars.File, Pos: pos})
	case vars.OpConditional:
		if v, _ := e.Lookup(name, sc); v != nil {
			return
		}
		set.Put(&vars.Var{Name: name, Value: value, Flavor: vars.Recursive, Origin: vars.File, Pos: pos})
	case vars.OpAppend:
		old := set.Get(name)
		if old == nil {
			set.Put(&vars.Var{Name: name, Value: value, Flavor: vars.Recursive, Origin: vars.File, Append: true, Pos: pos})
			return
		}
		add := value
		if old.Flavor == vars.Simple {
			add = e.Expand(value, sc)
		}
		set.Put(&vars.Var{Name: name, Value: vars.Paste(old.Value, add), Flavor: old.Flavor, Origin: vars.File, Append: old.Append, Pos: pos})
	}
}
DEFINE_GO

/usr/local/go/bin/gofmt -l . | tee /tmp/gofmt.out
test ! -s /tmp/gofmt.out
/usr/local/go/bin/go vet ./...
/usr/local/go/bin/go build -o /tmp/brickmake ./cmd/brickmake
