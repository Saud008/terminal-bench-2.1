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
