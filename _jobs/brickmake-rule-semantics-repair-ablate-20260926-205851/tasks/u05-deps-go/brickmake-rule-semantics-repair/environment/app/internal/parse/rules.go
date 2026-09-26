package parse

import (
	"strings"

	"brickmake/internal/db"
	"brickmake/internal/diag"
	"brickmake/internal/text"
	"brickmake/internal/vars"
)

// ignoredSpecial are special targets that are accepted and ignored.
var ignoredSpecial = map[string]bool{
	".SUFFIXES": true, ".DEFAULT": true, ".INTERMEDIATE": true, ".NOTINTERMEDIATE": true,
	".DELETE_ON_ERROR": true, ".IGNORE": true, ".SILENT": true, ".NOTPARALLEL": true,
	".ONESHELL": true, ".POSIX": true, ".EXPORT_ALL_VARIABLES": true, ".LOW_RESOLUTION_TIME": true,
}

// flush records the pending rule once all of its recipe lines are read.
func (p *Parser) flush() {
	r := p.rule
	if r == nil {
		return
	}
	p.rule = nil
	switch {
	case r.static:
		p.recordStatic(r)
	case strings.IndexByte(r.targets[0], '%') >= 0 || anyPattern(r.targets):
		for _, t := range r.targets {
			if strings.IndexByte(t, '%') < 0 {
				diag.Failf(r.pos, "mixed implicit and normal rules")
			}
		}
		p.DB.AddPatternRule(&db.PatternRule{Targets: r.targets, Prereqs: r.prereqs, Recipe: r.recipe, Pos: r.pos})
	default:
		p.recordExplicit(r)
	}
}

func anyPattern(targets []string) bool {
	for _, t := range targets {
		if strings.IndexByte(t, '%') >= 0 {
			return true
		}
	}
	return false
}

func (p *Parser) mention(pr db.Prereqs) {
	for _, w := range pr.Normal {
		p.DB.Enter(w)
	}
	for _, w := range pr.OrderOnly {
		p.DB.Enter(w)
	}
}

func (p *Parser) recordExplicit(r *pending) {
	for _, t := range r.targets {
		if p.special(t, r) {
			continue
		}
		p.addRule(p.DB.Enter(t), &db.Rule{Prereqs: r.prereqs, Recipe: r.recipe, Pos: r.pos})
		p.mention(r.prereqs)
	}
	p.defaultGoal(r.targets)
}

func (p *Parser) recordStatic(r *pending) {
	pat := text.ParsePattern(r.pattern)
	if !pat.Wild {
		diag.Failf(r.pos, "target pattern contains no '%%'")
	}
	for _, t := range r.targets {
		rule := &db.Rule{Recipe: r.recipe, Pos: r.pos, Static: true}
		stem, ok := pat.Match(t)
		if !ok {
			diag.Warn(r.pos, "target '%s' doesn't match the target pattern", t)
			rule.Stem = t
		} else {
			rule.Stem = stem
			if r.prereqs.Second {
				rule.Prereqs = r.prereqs
			} else {
				rule.Normal = substAll(r.prereqs.Normal, stem)
				rule.OrderOnly = substAll(r.prereqs.OrderOnly, stem)
			}
		}
		p.addRule(p.DB.Enter(t), rule)
		p.mention(rule.Prereqs)
	}
	p.defaultGoal(r.targets)
}

func substAll(words []string, stem string) []string {
	out := make([]string, len(words))
	for i, w := range words {
		out[i] = text.Subst(w, stem)
	}
	return out
}

func (p *Parser) addRule(f *db.File, r *db.Rule) {
	if r.Recipe != nil {
		if old := f.RecipeRule(); old != nil {
			diag.Warn(r.Recipe.Pos[0], "warning: overriding recipe for target '%s'", f.Name)
			diag.Warn(old.Recipe.Pos[0], "warning: ignoring old recipe for target '%s'", f.Name)
			old.Recipe = nil
		}
	}
	f.Rules = append(f.Rules, r)
}

// special handles special targets and reports whether t was one.
func (p *Parser) special(t string, r *pending) bool {
	words := append(append([]string{}, r.prereqs.Normal...), r.prereqs.OrderOnly...)
	if r.prereqs.Second {
		words = text.Fields(r.prereqs.Text)
	}
	switch {
	case t == ".PHONY":
		for _, w := range words {
			p.DB.Enter(w).Phony = true
		}
	case t == ".SECONDEXPANSION":
		p.second = true
	case t == ".PRECIOUS" || t == ".SECONDARY":
		if len(words) == 0 && t == ".SECONDARY" {
			p.DB.SecondaryAll = true
		}
		for _, w := range words {
			p.DB.Enter(w).Precious = true
		}
	case ignoredSpecial[t]:
	default:
		return false
	}
	return true
}

// defaultGoal makes the first ordinary target the default goal unless
// .DEFAULT_GOAL already has a value.
func (p *Parser) defaultGoal(targets []string) {
	if v := p.X.Global.Get(".DEFAULT_GOAL"); v != nil && v.Value != "" {
		return
	}
	for _, t := range targets {
		if strings.HasPrefix(t, ".") && strings.IndexByte(t, '/') < 0 {
			continue
		}
		p.X.DefineGlobal(".DEFAULT_GOAL", vars.OpRecursive, t, vars.File, diag.Pos{})
		return
	}
}
