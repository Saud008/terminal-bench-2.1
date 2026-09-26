package parse

import (
	"strings"

	"brickmake/internal/diag"
	"brickmake/internal/text"
)

type cond struct {
	active       bool // lines are currently read
	taken        bool // some branch was taken
	sawElse      bool
	parentActive bool
	pos          diag.Pos
}

func isConditional(word string) bool {
	switch word {
	case "ifdef", "ifndef", "ifeq", "ifneq", "else", "endif":
		return true
	}
	return false
}

func (p *Parser) skipping() bool {
	for _, c := range p.conds {
		if !c.active {
			return true
		}
	}
	return false
}

func (p *Parser) conditional(word, rest string, pos diag.Pos) {
	switch word {
	case "else":
		n := len(p.conds)
		if n == 0 {
			diag.Failf(pos, "extraneous 'else'")
		}
		c := &p.conds[n-1]
		if c.sawElse {
			diag.Failf(pos, "only one 'else' per conditional")
		}
		if text.TrimSpace(rest) == "" {
			c.sawElse = true
			c.active = c.parentActive && !c.taken
			c.taken = c.taken || c.active
			return
		}
		w, r := firstWord(rest)
		if w == "else" || w == "endif" || !isConditional(w) {
			diag.Failf(pos, "extraneous text after 'else' directive")
		}
		if c.parentActive && !c.taken {
			c.active = p.evaluate(w, r, pos)
			c.taken = c.active
		} else {
			c.active = false
		}
	case "endif":
		n := len(p.conds)
		if n == 0 {
			diag.Failf(pos, "extraneous 'endif'")
		}
		p.conds = p.conds[:n-1]
	default:
		parent := !p.skipping()
		val := false
		if parent {
			val = p.evaluate(word, rest, pos)
		}
		p.conds = append(p.conds, cond{active: parent && val, taken: parent && val, parentActive: parent, pos: pos})
	}
}

func (p *Parser) evaluate(word, rest string, pos diag.Pos) bool {
	switch word {
	case "ifdef", "ifndef":
		name := text.TrimSpace(p.X.Expand(rest, nil))
		v, _ := p.X.Lookup(name, nil)
		defined := v != nil && v.Value != ""
		return defined == (word == "ifdef")
	}
	a, b := eqArgs(word, rest, pos)
	equal := p.X.Expand(a, nil) == p.X.Expand(b, nil)
	return equal == (word == "ifeq")
}

// eqArgs splits the arguments of ifeq/ifneq. In the parenthesized form the
// first argument keeps its leading blanks but loses its trailing blanks;
// the second argument loses its leading blanks and keeps its trailing ones.
func eqArgs(word, s string, pos diag.Pos) (string, string) {
	s = text.TrimLeft(s)
	if s == "" {
		diag.Failf(pos, "invalid syntax in conditional")
	}
	var a, b, tail string
	if s[0] == '(' {
		body := s[1:]
		depth, i := 0, 0
		for ; i < len(body); i++ {
			c := body[i]
			if c == '(' {
				depth++
			} else if c == ')' {
				depth--
			} else if c == ',' && depth <= 0 {
				break
			}
		}
		if i >= len(body) {
			diag.Failf(pos, "invalid syntax in conditional")
		}
		a = strings.TrimRight(body[:i], " \t")
		r := text.TrimLeft(body[i+1:])
		depth = 0
		j := 0
		for ; j < len(r); j++ {
			if r[j] == '(' {
				depth++
			} else if r[j] == ')' {
				if depth == 0 {
					break
				}
				depth--
			}
		}
		if j >= len(r) {
			diag.Failf(pos, "invalid syntax in conditional")
		}
		b, tail = r[:j], r[j+1:]
	} else {
		q := s[0]
		if q != '"' && q != '\'' {
			diag.Failf(pos, "invalid syntax in conditional")
		}
		end := strings.IndexByte(s[1:], q)
		if end < 0 {
			diag.Failf(pos, "invalid syntax in conditional")
		}
		a = s[1 : 1+end]
		r := text.TrimLeft(s[2+end:])
		if r == "" || (r[0] != '"' && r[0] != '\'') {
			diag.Failf(pos, "invalid syntax in conditional")
		}
		q2 := r[0]
		end2 := strings.IndexByte(r[1:], q2)
		if end2 < 0 {
			diag.Failf(pos, "invalid syntax in conditional")
		}
		b, tail = r[1:1+end2], r[2+end2:]
	}
	if text.TrimSpace(tail) != "" {
		diag.Warn(pos, "extraneous text after '%s' directive", word)
	}
	return a, b
}
