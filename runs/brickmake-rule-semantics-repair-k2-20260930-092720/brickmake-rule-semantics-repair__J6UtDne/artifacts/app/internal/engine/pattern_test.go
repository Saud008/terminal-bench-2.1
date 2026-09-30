package engine

import (
	"testing"

	"brickmake/internal/db"
	"brickmake/internal/expand"
	"brickmake/internal/vars"
)

func testEngine(d *db.DB) *Engine {
	g := vars.NewSet()
	return New(d, expand.New(g))
}

func TestCandidatesOrderByFullStem(t *testing.T) {
	d := db.New()
	slash := &db.PatternRule{Targets: []string{"lib/%.o"}}
	plain := &db.PatternRule{Targets: []string{"%.o"}}
	// Put the less-specific rule first to ensure sorting, not definition
	// order, chooses the rule with the shorter directory-inclusive stem.
	d.PatternRules = []*db.PatternRule{plain, slash}
	cs := testEngine(d).candidates("lib/a.o", nil)
	if len(cs) != 2 {
		t.Fatalf("got %d candidates, want 2", len(cs))
	}
	if cs[0].rule != slash || cs[0].fullStem() != "a" {
		t.Fatalf("first candidate = rule %p stem %q; want slash rule, stem a", cs[0].rule, cs[0].fullStem())
	}
}

func TestDirectoryRelativePrerequisites(t *testing.T) {
	d := db.New()
	r := &db.PatternRule{
		Targets: []string{"%.o"},
		Prereqs: db.Prereqs{Normal: []string{"%.c", "config.h"}, OrderOnly: []string{"gen/%"}},
	}
	e := testEngine(d)
	normal, order := e.prereqs(candidate{rule: r, dir: "net/", stem: "sock"}, "net/sock.o", nil)
	if got, want := normal, []string{"net/sock.c", "config.h"}; !sameStrings(got, want) {
		t.Fatalf("normal prerequisites = %v, want %v", got, want)
	}
	if got, want := order, []string{"net/gen/sock"}; !sameStrings(got, want) {
		t.Fatalf("order-only prerequisites = %v, want %v", got, want)
	}
}

func TestPatternVariablesAppliedBySpecificity(t *testing.T) {
	d := db.New()
	d.PatternVars = []*db.PatternVar{
		{Pattern: "build/net/%.o", Name: "CFLAGS", Op: vars.OpAppend, Value: "-DNET"},
		{Pattern: "build/%.o", Name: "CFLAGS", Op: vars.OpAppend, Value: "-fPIC"},
	}
	e := testEngine(d)
	e.x.Global.Put(&vars.Var{Name: "CFLAGS", Value: "-O2", Flavor: vars.Recursive, Origin: vars.File})
	n := e.node(d.Enter("build/net/sock.o"))
	if got, want := e.x.Expand("$(CFLAGS)", e.scope(n)), "-O2 -fPIC -DNET"; got != want {
		t.Fatalf("CFLAGS = %q, want %q", got, want)
	}
}

func sameStrings(a, b []string) bool {
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
