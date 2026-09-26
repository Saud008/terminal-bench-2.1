package expand

import (
	"fmt"
	"strconv"
	"strings"

	"brickmake/internal/diag"
	"brickmake/internal/text"
	"brickmake/internal/vars"
)

func fnForeach(e *Expander, a []string, sc *Scope) string {
	name := text.TrimSpace(e.Expand(a[0], sc))
	words := text.Fields(e.Expand(a[1], sc))
	var b strings.Builder
	for _, w := range words {
		set := vars.NewSet()
		set.Put(&vars.Var{Name: name, Value: w, Flavor: vars.Simple, Origin: vars.Automatic})
		b.WriteString(e.Expand(a[2], sc.With(set)))
		b.WriteByte(' ')
	}
	out := b.String()
	if out != "" {
		out = out[:len(out)-1]
	}
	return out
}

func fnIf(e *Expander, a []string, sc *Scope) string {
	if e.Expand(text.TrimSpace(a[0]), sc) != "" {
		return e.Expand(a[1], sc)
	}
	if len(a) > 2 {
		return e.Expand(a[2], sc)
	}
	return ""
}

func fnOr(e *Expander, a []string, sc *Scope) string {
	for _, arg := range a {
		if r := e.Expand(text.TrimSpace(arg), sc); r != "" {
			return r
		}
	}
	return ""
}

func fnAnd(e *Expander, a []string, sc *Scope) string {
	r := ""
	for _, arg := range a {
		if r = e.Expand(text.TrimSpace(arg), sc); r == "" {
			return ""
		}
	}
	return r
}

// fnCall binds $(0), $(1), ... and expands the named variable. A variable
// may call itself through $(call).
func fnCall(e *Expander, a []string, sc *Scope) string {
	name := text.TrimSpace(a[0])
	if fn, ok := functions[name]; ok && name != "call" {
		args := a[1:]
		if len(args) < fn.min {
			diag.Failf(e.Pos, "insufficient number of arguments (%d) to function '%s'", len(args), name)
		}
		if fn.max > 0 && len(args) > fn.max {
			args = append(args[:fn.max-1:fn.max-1], strings.Join(args[fn.max-1:], ","))
		}
		return fn.run(e, args, sc)
	}
	v, rest := e.Lookup(name, sc)
	if v == nil {
		return ""
	}
	set := vars.NewSet()
	n := len(a)
	if n < 10 {
		n = 10
	}
	for i := 0; i < n; i++ {
		val := ""
		if i == 0 {
			val = name
		} else if i < len(a) {
			val = a[i]
		}
		set.Put(&vars.Var{Name: strconv.Itoa(i), Value: val, Flavor: vars.Simple, Origin: vars.Automatic})
	}
	inner := sc.With(set)
	if v.Append {
		return e.appended(v, rest, inner)
	}
	if v.Flavor == vars.Simple {
		return v.Value
	}
	return e.expandAt(v, inner)
}

func (e *Expander) lookupNamed(arg string, sc *Scope) (string, *vars.Var) {
	name := text.TrimSpace(arg)
	v, _ := e.Lookup(name, sc)
	return name, v
}

func fnOrigin(e *Expander, a []string, sc *Scope) string {
	name, v := e.lookupNamed(a[0], sc)
	if sc != nil && sc.Auto != nil && IsAutomatic(name) {
		return vars.Automatic.String()
	}
	if v == nil {
		return vars.Undefined.String()
	}
	return v.Origin.String()
}

func fnFlavor(e *Expander, a []string, sc *Scope) string {
	_, v := e.lookupNamed(a[0], sc)
	if v == nil {
		return "undefined"
	}
	return v.Flavor.String()
}

func fnValue(e *Expander, a []string, sc *Scope) string {
	name, v := e.lookupNamed(a[0], sc)
	if sc != nil && sc.Auto != nil {
		if val, ok := sc.Auto.Value(name); ok {
			return val
		}
	}
	if v == nil {
		return ""
	}
	return v.Value
}

func fnInfo(e *Expander, a []string, _ *Scope) string {
	fmt.Fprintln(diag.Stdout, a[0])
	return ""
}

func fnWarning(e *Expander, a []string, _ *Scope) string {
	diag.Warn(e.Pos, "%s", a[0])
	return ""
}

func fnError(e *Expander, a []string, _ *Scope) string {
	diag.Failf(e.Pos, "%s", a[0])
	return ""
}

func fnShell(e *Expander, a []string, _ *Scope) string {
	if e.Shell == nil {
		return ""
	}
	out := strings.TrimRight(e.Shell(a[0]), "\n")
	out = strings.ReplaceAll(out, "\r\n", " ")
	return strings.ReplaceAll(out, "\n", " ")
}
