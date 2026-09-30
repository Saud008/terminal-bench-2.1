package engine

import (
	"reflect"
	"testing"

	"brickmake/internal/db"
	"brickmake/internal/diag"
	"brickmake/internal/expand"
	"brickmake/internal/vars"
)

func testEngine(d *db.DB) *Engine {
	x := expand.New(vars.NewSet())
	return New(d, x)
}

func TestCandidatesSortByFullStem(t *testing.T) {
	d := db.New()
	generic := &db.PatternRule{Targets: []string{"%.o"}}
	specific := &db.PatternRule{Targets: []string{"lib/%.o"}}
	d.PatternRules = []*db.PatternRule{generic, specific}
	e := testEngine(d)
	got := e.candidates("lib/a.o", map[*db.PatternRule]bool{})
	if len(got) != 2 || got[0].rule != specific || got[0].fullStem() != "a" || got[1].fullStem() != "lib/a" {
		t.Fatalf("candidates = %#v", got)
	}
}

func TestDirectoryRelativePrerequisites(t *testing.T) {
	d := db.New()
	r := &db.PatternRule{
		Targets: []string{"%.o"},
		Prereqs: db.Prereqs{
			Normal:    []string{"%.c", "config.h"},
			OrderOnly: []string{"%dir", "stamp"},
		},
	}
	e := testEngine(d)
	c := candidate{rule: r, dir: "net/", stem: "sock"}
	normal, order := e.prereqs(c, "net/sock.o", nil)
	if want := []string{"net/sock.c", "config.h"}; !reflect.DeepEqual(normal, want) {
		t.Fatalf("normal = %q, want %q", normal, want)
	}
	if want := []string{"net/sockdir", "stamp"}; !reflect.DeepEqual(order, want) {
		t.Fatalf("order-only = %q, want %q", order, want)
	}
}

func TestPatternVariablesLeastSpecificFirst(t *testing.T) {
	d := db.New()
	d.PatternVars = []*db.PatternVar{
		{Pattern: "build/net/%.o", Name: "CFLAGS", Op: vars.OpAppend, Value: "-DNET"},
		{Pattern: "build/%.o", Name: "CFLAGS", Op: vars.OpAppend, Value: "-fPIC"},
	}
	x := expand.New(vars.NewSet())
	x.DefineGlobal("CFLAGS", vars.OpRecursive, "-O2", vars.File, diag.Pos{})
	e := New(d, x)
	n := e.node(d.Enter("build/net/sock.o"))
	got := x.Expand("$(CFLAGS)", e.scope(n))
	if got != "-O2 -fPIC -DNET" {
		t.Fatalf("CFLAGS = %q", got)
	}
}
