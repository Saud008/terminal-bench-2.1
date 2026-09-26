// Package db is the rule database built by the parser and read by the
// engine.
package db

import (
	"brickmake/internal/diag"
	"brickmake/internal/vars"
)

// Recipe is the list of raw recipe lines of one rule.
type Recipe struct {
	Lines []string
	Pos   []diag.Pos // position of each line
}

// Prereqs is the prerequisite list of one rule line. With secondary
// expansion Text is expanded again when the target is considered and
// split into normal and order-only words afterwards.
type Prereqs struct {
	Normal    []string
	OrderOnly []string
	Text      string
	Second    bool
}

// Rule is one explicit rule line for a target (static pattern rules
// produce one Rule per target).
type Rule struct {
	Prereqs
	Recipe *Recipe
	Stem   string // static pattern rules only
	Static bool
	Pos    diag.Pos
}

// File is a target or prerequisite mentioned in the makefile or entered by
// implicit rule search.
type File struct {
	Name  string
	Rules []*Rule
	Phony bool
	// Precious files are never removed as intermediates.
	Precious bool
	Vars     *vars.Set
}

// RecipeRule returns the rule whose recipe the file uses, or nil.
func (f *File) RecipeRule() *Rule {
	var r *Rule
	for _, x := range f.Rules {
		if x.Recipe != nil {
			r = x
		}
	}
	return r
}

// PatternRule is an implicit rule: every target contains '%'.
type PatternRule struct {
	Targets []string
	Prereqs
	Recipe *Recipe
	Pos    diag.Pos
}

// PatternVar is one pattern-specific assignment.
type PatternVar struct {
	Pattern string
	Name    string
	Op      vars.Op
	Value   string // already expanded for ":="
	Pos     diag.Pos
}

// DB is the result of reading the makefiles.
type DB struct {
	Files        map[string]*File
	Order        []*File
	PatternRules []*PatternRule
	PatternVars  []*PatternVar
	// SecondaryAll is set by a .SECONDARY rule without prerequisites.
	SecondaryAll bool
}

func New() *DB { return &DB{Files: map[string]*File{}} }

// Lookup returns the file entry for name, or nil.
func (d *DB) Lookup(name string) *File { return d.Files[name] }

// Enter returns the file entry for name, creating it if needed.
func (d *DB) Enter(name string) *File {
	if f := d.Files[name]; f != nil {
		return f
	}
	f := &File{Name: name, Vars: vars.NewSet()}
	d.Files[name] = f
	d.Order = append(d.Order, f)
	return f
}

func sameWords(a, b []string) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

// AddPatternRule installs a pattern rule. A rule with the same targets and
// prerequisites as an existing one replaces it and moves to the end; a
// rule without a recipe only cancels such a rule.
func (d *DB) AddPatternRule(r *PatternRule) {
	for i, old := range d.PatternRules {
		if sameWords(old.Targets, r.Targets) && sameWords(old.Normal, r.Normal) && old.Text == r.Text {
			d.PatternRules = append(d.PatternRules[:i:i], d.PatternRules[i+1:]...)
			break
		}
	}
	if r.Recipe != nil {
		d.PatternRules = append(d.PatternRules, r)
	}
}
