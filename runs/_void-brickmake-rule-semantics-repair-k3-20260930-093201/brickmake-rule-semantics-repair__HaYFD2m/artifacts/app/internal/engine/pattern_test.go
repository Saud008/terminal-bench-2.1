package engine

import (
	"reflect"
	"testing"

	"brickmake/internal/db"
	"brickmake/internal/diag"
	"brickmake/internal/expand"
	"brickmake/internal/vars"
)

func testEngine() *Engine {
	d := db.New()
	x := expand.New(vars.NewSet())
	return New(d, x)
}

func TestCandidatesSortByFullStem(t *testing.T) {
	e := testEngine()
	whole := &db.PatternRule{Targets: []string{"lib/%.o"}}
	relative := &db.PatternRule{Targets: []string{"%.o"}}
	e.db.PatternRules = []*db.PatternRule{relative, whole}
	got := e.candidates("lib/a.o", map[*db.PatternRule]bool{})
	if len(got) != 2 || got[0].rule != whole || got[1].rule != relative {
		t.Fatalf("wrong candidate order: %#v", got)
	}
}

func TestDirectoryRelativePrerequisites(t *testing.T) {
	e := testEngine()
	c := candidate{
		rule: &db.PatternRule{Prereqs: db.Prereqs{
			Normal:    []string{"%.c", "config.h"},
			OrderOnly: []string{"dirs/%"},
		}},
		dir: "net/", stem: "sock",
	}
	normal, order := e.prereqs(c, "net/sock.o", nil)
	if !reflect.DeepEqual(normal, []string{"net/sock.c", "config.h"}) ||
		!reflect.DeepEqual(order, []string{"net/dirs/sock"}) {
		t.Fatalf("prereqs = %v | %v", normal, order)
	}
}

func TestMentionedPrerequisiteOughtToExist(t *testing.T) {
	e := testEngine()
	e.db.Enter("goal-only")
	if e.oughtToExist("goal-only") {
		t.Fatal("unmentioned entry should not ought to exist")
	}
	e.db.Enter("generated.h").Mentioned = true
	if !e.oughtToExist("generated.h") {
		t.Fatal("mentioned prerequisite should ought to exist")
	}
}

func TestPatternVariablesSpecificityOrder(t *testing.T) {
	e := testEngine()
	e.x.DefineGlobal("CFLAGS", vars.OpRecursive, "-O2", vars.File, diag.Pos{})
	e.db.PatternVars = []*db.PatternVar{
		{Pattern: "build/net/%.o", Name: "CFLAGS", Op: vars.OpAppend, Value: "-DNET"},
		{Pattern: "build/%.o", Name: "CFLAGS", Op: vars.OpAppend, Value: "-fPIC"},
	}
	n := e.node(e.db.Enter("build/net/sock.o"))
	got := e.x.Expand("$(CFLAGS)", e.scope(n))
	if got != "-O2 -fPIC -DNET" {
		t.Fatalf("CFLAGS = %q", got)
	}
}
