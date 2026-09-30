// Package expand implements variable and function expansion.
package expand

import (
	"strings"

	"brickmake/internal/diag"
	"brickmake/internal/text"
	"brickmake/internal/vars"
)

// Scope is the variable context of one expansion. Sets are searched
// innermost first; the global set is always searched last.
type Scope struct {
	Sets []*vars.Set
	Auto *Auto
}

// With returns a scope with set searched before everything in sc.
func (sc *Scope) With(set *vars.Set) *Scope {
	n := &Scope{Sets: []*vars.Set{set}}
	if sc != nil {
		n.Sets = append(n.Sets, sc.Sets...)
		n.Auto = sc.Auto
	}
	return n
}

// Expander expands makefile text.
type Expander struct {
	Global *vars.Set
	// Pos is the makefile position reported by $(info), $(warning),
	// $(error) and expansion errors.
	Pos diag.Pos
	// Shell runs $(shell ...) commands.
	Shell func(cmd string) string

	active map[*vars.Var]bool
}

func New(global *vars.Set) *Expander {
	return &Expander{Global: global, active: map[*vars.Var]bool{}}
}

func (e *Expander) chain(sc *Scope) []*vars.Set {
	if sc == nil {
		return []*vars.Set{e.Global}
	}
	out := make([]*vars.Set, 0, len(sc.Sets)+1)
	out = append(out, sc.Sets...)
	return append(out, e.Global)
}

// Lookup finds the definition of name visible in sc and the sets that
// enclose it.
func (e *Expander) Lookup(name string, sc *Scope) (*vars.Var, []*vars.Set) {
	sets := e.chain(sc)
	for i, s := range sets {
		if v := s.Get(name); v != nil {
			return v, sets[i+1:]
		}
	}
	return nil, nil
}

// Value returns the expanded value of variable name.
func (e *Expander) Value(name string, sc *Scope) string {
	if sc != nil && sc.Auto != nil {
		if v, ok := sc.Auto.Value(name); ok {
			return v
		}
	}
	v, rest := e.Lookup(name, sc)
	if v == nil {
		return ""
	}
	if v.Append {
		return e.appended(v, rest, sc)
	}
	return e.plain(v, sc)
}

func (e *Expander) plain(v *vars.Var, sc *Scope) string {
	if v.Flavor == vars.Simple {
		return v.Value
	}
	if e.active[v] {
		diag.Failf(v.Pos, "Recursive variable '%s' references itself (eventually)", v.Name)
	}
	e.active[v] = true
	defer delete(e.active, v)
	return e.expandAt(v, sc)
}

// expandAt expands a recursive variable's text; messages raised while
// doing so report the variable's definition.
func (e *Expander) expandAt(v *vars.Var, sc *Scope) string {
	if v.Pos.Valid() {
		saved := e.Pos
		e.Pos = v.Pos
		defer func() { e.Pos = saved }()
	}
	return e.Expand(v.Value, sc)
}

// appended builds the value of a target- or pattern-specific "+="
// definition: the value visible from the enclosing sets, a space when that
// value is not empty, then this definition's own text.
func (e *Expander) appended(v *vars.Var, rest []*vars.Set, sc *Scope) string {
	buf := ""
	for i, s := range rest {
		u := s.Get(v.Name)
		if u == nil {
			continue
		}
		if u.Append {
			buf = e.appended(u, rest[i+1:], sc)
		} else {
			buf = e.plain(u, sc)
		}
		break
	}
	if buf != "" {
		buf += " "
	}
	return buf + e.plain(v, sc)
}

// closing returns the index of the delimiter that closes an opening
// delimiter whose body starts at s[i]. Only delimiters of the same kind
// are counted.
func closing(s string, i int, open, close byte) int {
	depth := 0
	for ; i < len(s); i++ {
		switch s[i] {
		case open:
			depth++
		case close:
			if depth == 0 {
				return i
			}
			depth--
		}
	}
	return -1
}

// Expand expands all variable references and function calls in s.
func (e *Expander) Expand(s string, sc *Scope) string {
	if strings.IndexByte(s, '$') < 0 {
		return s
	}
	var b strings.Builder
	for i := 0; i < len(s); {
		c := s[i]
		if c != '$' {
			j := strings.IndexByte(s[i:], '$')
			if j < 0 {
				b.WriteString(s[i:])
				break
			}
			b.WriteString(s[i : i+j])
			i += j
			continue
		}
		if i+1 >= len(s) {
			break
		}
		n := s[i+1]
		switch n {
		case '$':
			b.WriteByte('$')
			i += 2
		case '(', '{':
			close := byte(')')
			if n == '{' {
				close = '}'
			}
			end := closing(s, i+2, n, close)
			if end < 0 {
				e.unterminated(s[i+2:], n, close)
			}
			b.WriteString(e.reference(s[i+2:end], n, close, sc))
			i = end + 1
		default:
			b.WriteString(e.Value(string(n), sc))
			i += 2
		}
	}
	return b.String()
}

func (e *Expander) unterminated(body string, open, close byte) {
	name := body
	if k := strings.IndexAny(name, " \t"); k >= 0 {
		name = name[:k]
		if _, ok := functions[name]; ok {
			diag.Failf(e.Pos, "unterminated call to function '%s': missing '%c'", name, close)
		}
	}
	diag.Failf(e.Pos, "unterminated variable reference")
}

// reference expands the body of $(...) or ${...}.
func (e *Expander) reference(body string, open, close byte, sc *Scope) string {
	if k := strings.IndexAny(body, " \t"); k > 0 {
		if fn, ok := functions[body[:k]]; ok {
			return e.call(fn, body[:k], text.TrimLeft(body[k:]), open, close, sc)
		}
	}
	name := body
	if strings.IndexByte(name, '$') >= 0 {
		name = e.Expand(name, sc)
	}
	if colon := strings.IndexByte(name, ':'); colon >= 0 {
		if eq := strings.IndexByte(name[colon+1:], '='); eq >= 0 {
			from := name[colon+1 : colon+1+eq]
			to := name[colon+2+eq:]
			value := e.Value(name[:colon], sc)
			if strings.IndexByte(from, '%') < 0 {
				from, to = "%"+from, "%"+to
			}
			return text.Patsubst(from, to, value)
		}
	}
	return e.Value(name, sc)
}

// splitArgs splits function arguments at top-level commas. The last of
// max arguments receives the rest of the text, commas included.
func splitArgs(s string, open, close byte, max int) []string {
	var args []string
	depth, start := 0, 0
	for i := 0; i < len(s); i++ {
		switch s[i] {
		case open:
			depth++
		case close:
			depth--
		case ',':
			if depth == 0 && (max == 0 || len(args) < max-1) {
				args = append(args, s[start:i])
				start = i + 1
			}
		}
	}
	return append(args, s[start:])
}
