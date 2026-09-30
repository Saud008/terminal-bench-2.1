package engine

import (
	"reflect"
	"testing"

	"brickmake/internal/db"
	"brickmake/internal/expand"
	"brickmake/internal/vars"
)

func testEngine(d *db.DB) *Engine {
	x := expand.New(vars.NewSet())
	return New(d, x)
}

func recipe(s string) *db.Recipe { return &db.Recipe{Lines: []string{s}} }

func TestPatternSetSpecificityOrder(t *testing.T) {
	d := db.New()
	d.PatternVars = []*db.PatternVar{
		{Pattern: "build/net/%.o", Name: "CFLAGS", Op: vars.OpAppend, Value: "-DNET"},
		{Pattern: "build/%.o", Name: "CFLAGS", Op: vars.OpAppend, Value: "-fPIC"},
	}
	e := testEngine(d)
	e.x.DefineGlobal("CFLAGS", vars.OpRecursive, "-O2", vars.File, db.PatternVar{}.Pos)
	n := e.node(d.Enter("build/net/sock.o"))
	sc := e.scope(n)
	if got := e.x.Expand("$(CFLAGS)", sc); got != "-O2 -fPIC -DNET" {
		t.Fatalf("CFLAGS = %q", got)
	}
}

func TestCandidatesUseFullStemLength(t *testing.T) {
	d := db.New()
	generic := &db.PatternRule{Targets: []string{"%.out"}, Recipe: recipe("generic")}
	specific := &db.PatternRule{Targets: []string{"lib/%.out"}, Recipe: recipe("specific")}
	d.PatternRules = []*db.PatternRule{generic, specific}
	cs := testEngine(d).candidates("lib/a.out", map[*db.PatternRule]bool{})
	if len(cs) != 2 || cs[0].rule != specific || cs[1].rule != generic {
		t.Fatalf("candidate order = %#v", cs)
	}
}

func TestDirectoryRelativePrereqsPrefixOnlyPatterns(t *testing.T) {
	d := db.New()
	r := &db.PatternRule{Targets: []string{"%.o"}, Prereqs: db.Prereqs{
		Normal: []string{"%.c", "config.h"}, OrderOnly: []string{"%/dir", "stamp"},
	}}
	e := testEngine(d)
	c := candidate{rule: r, dir: "net/", stem: "sock"}
	normal, order := e.prereqs(c, "net/sock.o", nil)
	if !reflect.DeepEqual(normal, []string{"net/sock.c", "config.h"}) ||
		!reflect.DeepEqual(order, []string{"net/sock/dir", "stamp"}) {
		t.Fatalf("prereqs = %q | %q", normal, order)
	}
}

func TestMentionedPrerequisiteOughtToExist(t *testing.T) {
	d := db.New()
	d.Enter("generated.h")
	if !testEngine(d).oughtToExist("generated.h") {
		t.Fatal("mentioned prerequisite should ought to exist")
	}
}

func TestPatternRulesDifferingInOrderOnlyPrereqsAreDistinct(t *testing.T) {
	d := db.New()
	d.AddPatternRule(&db.PatternRule{
		Targets: []string{"%.o"},
		Prereqs: db.Prereqs{Normal: []string{"%.c"}, OrderOnly: []string{"one"}},
		Recipe:  recipe("one"),
	})
	d.AddPatternRule(&db.PatternRule{
		Targets: []string{"%.o"},
		Prereqs: db.Prereqs{Normal: []string{"%.c"}, OrderOnly: []string{"two"}},
		Recipe:  recipe("two"),
	})
	if len(d.PatternRules) != 2 {
		t.Fatalf("pattern rules = %d, want 2", len(d.PatternRules))
	}
}
