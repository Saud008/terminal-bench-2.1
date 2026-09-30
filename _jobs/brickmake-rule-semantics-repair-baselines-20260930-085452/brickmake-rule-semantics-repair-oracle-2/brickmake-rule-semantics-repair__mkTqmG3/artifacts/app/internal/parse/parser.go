// Package parse reads makefiles into a db.DB.
package parse

import (
	"strings"

	"brickmake/internal/db"
	"brickmake/internal/diag"
	"brickmake/internal/expand"
	"brickmake/internal/text"
	"brickmake/internal/vars"
)

var unsupported = map[string]bool{
	"define": true, "endef": true, "include": true, "-include": true, "sinclude": true,
	"override": true, "export": true, "unexport": true, "vpath": true, "undefine": true,
	"private": true, "load": true,
}

// pending is a rule line whose recipe lines are still being read.
type pending struct {
	targets []string
	prereqs db.Prereqs
	static  bool
	pattern string
	recipe  *db.Recipe
	pos     diag.Pos
}

// Parser reads one or more makefiles into DB.
type Parser struct {
	DB *db.DB
	X  *expand.Expander

	file   string
	lines  []string
	next   int
	conds  []cond
	rule   *pending
	second bool
}

func New(d *db.DB, x *expand.Expander) *Parser { return &Parser{DB: d, X: x} }

// Parse reads the makefile text src named name.
func (p *Parser) Parse(name string, src []byte) {
	p.file = name
	p.lines = strings.Split(strings.ReplaceAll(string(src), "\r\n", "\n"), "\n")
	p.next = 0
	for p.next < len(p.lines) {
		pos := diag.Pos{File: name, Line: p.next + 1}
		raw := p.lines[p.next]
		p.next++
		if strings.HasPrefix(raw, "\t") && p.rule != nil {
			line := raw[1:]
			for oddBackslashes(line) && p.next < len(p.lines) {
				line += "\n" + strings.TrimPrefix(p.lines[p.next], "\t")
				p.next++
			}
			if !p.skipping() {
				p.addRecipeLine(line, pos)
			}
			continue
		}
		line := raw
		for oddBackslashes(line) && p.next < len(p.lines) {
			line = strings.TrimRight(line[:len(line)-1], " \t")
			line += " " + strings.TrimLeft(p.lines[p.next], " \t")
			p.next++
		}
		p.statement(line, pos)
	}
	p.flush()
	if n := len(p.conds); n > 0 {
		diag.Failf(p.conds[n-1].pos, "missing 'endif'")
	}
}

func (p *Parser) addRecipeLine(line string, pos diag.Pos) {
	if p.rule.recipe == nil {
		p.rule.recipe = &db.Recipe{}
	}
	p.rule.recipe.Lines = append(p.rule.recipe.Lines, line)
	p.rule.recipe.Pos = append(p.rule.recipe.Pos, pos)
}

func firstWord(s string) (word, rest string) {
	s = text.TrimLeft(s)
	i := strings.IndexAny(s, " \t")
	if i < 0 {
		return s, ""
	}
	return s[:i], text.TrimLeft(s[i:])
}

func (p *Parser) statement(line string, pos diag.Pos) {
	p.X.Pos = pos
	body := text.TrimLeft(stripComment(line))
	if text.TrimSpace(body) == "" {
		return
	}
	word, rest := firstWord(body)
	if isConditional(word) {
		p.conditional(word, rest, pos)
		return
	}
	if p.skipping() {
		return
	}
	if unsupported[word] && !startsAssignment(rest) {
		diag.Failf(pos, "unsupported directive '%s'", word)
	}
	if name, op, value, ok := scanAssign(body); ok {
		p.flush()
		p.assign(name, op, value, pos)
		return
	}
	p.flush()
	p.ruleLine(text.TrimLeft(line), pos)
}

func startsAssignment(rest string) bool {
	for _, op := range []string{"=", ":=", "::=", "+=", "?="} {
		if strings.HasPrefix(rest, op) {
			return true
		}
	}
	return strings.HasPrefix(rest, ":")
}

func (p *Parser) assign(name string, op vars.Op, value string, pos diag.Pos) {
	name = text.TrimSpace(p.X.Expand(name, nil))
	if name == "" {
		diag.Failf(pos, "empty variable name")
	}
	p.X.DefineGlobal(name, op, value, vars.File, pos)
}

func (p *Parser) ruleLine(line string, pos diag.Pos) {
	ruleText, recipe := splitRecipe(line)
	colon := findTop(ruleText, ':')
	if colon < 0 {
		if text.TrimSpace(p.X.Expand(ruleText, nil)) == "" {
			return
		}
		diag.Failf(pos, "missing separator")
	}
	rest := ruleText[colon+1:]
	if strings.HasPrefix(rest, ":") {
		diag.Failf(pos, "double-colon rules are not supported")
	}
	targets := text.Fields(p.X.Expand(ruleText[:colon], nil))
	if len(targets) == 0 {
		diag.Failf(pos, "missing target")
	}
	if name, op, value, ok := scanAssign(text.TrimLeft(rest)); ok {
		if recipe != nil {
			value += ";" + stripComment(*recipe)
		}
		name = text.TrimSpace(p.X.Expand(name, nil))
		if name == "" {
			diag.Failf(pos, "empty variable name")
		}
		p.targetVar(targets, name, op, value, pos)
		return
	}
	r := &pending{targets: targets, pos: pos}
	prereqText := rest
	if c := findTop(rest, ':'); c >= 0 {
		r.static = true
		r.pattern = text.TrimSpace(p.X.Expand(rest[:c], nil))
		prereqText = rest[c+1:]
	}
	expanded := p.X.Expand(prereqText, nil)
	if p.second {
		r.prereqs = db.Prereqs{Text: expanded, Second: true}
	} else {
		r.prereqs.Normal, r.prereqs.OrderOnly = text.SplitOrder(text.Fields(expanded))
	}
	p.rule = r
	if recipe != nil {
		p.addRecipeLine(*recipe, pos)
	}
}

// targetVar records "targets: name op value".
func (p *Parser) targetVar(targets []string, name string, op vars.Op, value string, pos diag.Pos) {
	for _, t := range targets {
		if strings.IndexByte(t, '%') >= 0 {
			v := value
			if op == vars.OpSimple {
				v = p.X.Expand(value, nil)
			}
			p.DB.PatternVars = append(p.DB.PatternVars, &db.PatternVar{Pattern: t, Name: name, Op: op, Value: v, Pos: pos})
			continue
		}
		f := p.DB.Enter(t)
		p.X.DefineIn(f.Vars, name, op, value, pos)
	}
}
