package engine

import (
	"reflect"
	"testing"

	"brickmake/internal/db"
	"brickmake/internal/diag"
	"brickmake/internal/expand"
	"brickmake/internal/vars"
)

func patternEngine() *Engine {
	g := vars.NewSet()
	return &Engine{db: db.New(), x: expand.New(g), nodes: map[*db.File]*node{}}
}

func TestPatternVarsAppliedShortestPatternFirst(t *testing.T) {
	e := patternEngine()
	e.x.DefineGlobal("CFLAGS", vars.OpRecursive, "-O2", vars.File, diag.Pos{})
	// Reverse the desired order so makefile order cannot hide the required
	// least-specific-to-most-specific application order.
	e.db.PatternVars = []*db.PatternVar{
		{Pattern: "build/net/%.o", Name: "CFLAGS", Op: vars.OpAppend, Value: "-DNET"},
		{Pattern: "build/%.o", Name: "CFLAGS", Op: vars.OpAppend, Value: "-fPIC"},
	}
	n := e.node(e.db.Enter("build/net/sock.o"))
	if got := e.x.Value("CFLAGS", e.scope(n)); got != "-O2 -fPIC -DNET" {
		t.Fatalf("CFLAGS = %q", got)
	}
}

func TestCandidatesSortByFullStem(t *testing.T) {
	e := patternEngine()
	whole := &db.PatternRule{Targets: []string{"lib/%.o"}}
	relative := &db.PatternRule{Targets: []string{"%.o"}}
	e.db.PatternRules = []*db.PatternRule{relative, whole}
	cs := e.candidates("lib/a.o", map[*db.PatternRule]bool{})
	if len(cs) != 2 || cs[0].rule != whole {
		t.Fatalf("candidate order = %#v", cs)
	}
}

func TestDirectoryRelativePrerequisites(t *testing.T) {
	e := patternEngine()
	c := candidate{
		rule: &db.PatternRule{Prereqs: db.Prereqs{
			Normal:    []string{"%.c", "config.h"},
			OrderOnly: []string{"generated/%"},
		}},
		dir: "net/", stem: "sock",
	}
	normal, order := e.prereqs(c, "net/sock.o", nil)
	if !reflect.DeepEqual(normal, []string{"net/sock.c", "config.h"}) {
		t.Fatalf("normal prerequisites = %#v", normal)
	}
	if !reflect.DeepEqual(order, []string{"net/generated/sock"}) {
		t.Fatalf("order-only prerequisites = %#v", order)
	}
}

func TestMentionedPrerequisiteOughtToExist(t *testing.T) {
	e := patternEngine()
	// A prerequisite mentioned by an explicit rule is entered in the database
	// even when it has no rule of its own.
	e.db.Enter("source.x")
	r := &db.PatternRule{
		Targets: []string{"%.out"},
		Prereqs: db.Prereqs{Normal: []string{"source.x"}},
	}
	e.db.PatternRules = []*db.PatternRule{r}
	m := e.findImplicit("result.out", nil, 0, map[*db.PatternRule]bool{})
	if m == nil || m.rule != r {
		t.Fatal("rule with mentioned prerequisite was not selected in pass one")
	}
}

func TestCommandLineVariableOverridesPatternAssignment(t *testing.T) {
	e := patternEngine()
	e.x.DefineGlobal("CFLAGS", vars.OpRecursive, "-DCMD", vars.CommandLine, diag.Pos{})
	e.db.PatternVars = []*db.PatternVar{
		{Pattern: "%.o", Name: "CFLAGS", Op: vars.OpAppend, Value: "-fPIC"},
	}
	n := e.node(e.db.Enter("file.o"))
	if got := e.x.Value("CFLAGS", e.scope(n)); got != "-DCMD" {
		t.Fatalf("CFLAGS = %q, want command-line value", got)
	}
}
