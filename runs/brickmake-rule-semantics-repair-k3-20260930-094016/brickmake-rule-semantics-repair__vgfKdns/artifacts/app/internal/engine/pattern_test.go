package engine

import (
	"reflect"
	"testing"

	"brickmake/internal/db"
	"brickmake/internal/diag"
	"brickmake/internal/expand"
	"brickmake/internal/vars"
)

func testEngine() (*Engine, *db.DB, *expand.Expander) {
	d := db.New()
	x := expand.New(vars.NewSet())
	return New(d, x), d, x
}

func TestPatternVariablesApplyGenericBeforeSpecific(t *testing.T) {
	e, d, x := testEngine()
	x.DefineGlobal("CFLAGS", vars.OpRecursive, "-O2", vars.File, diag.Pos{})
	// Deliberately put the more-specific pattern first: specificity, not
	// makefile order, determines the resulting value.
	d.PatternVars = append(d.PatternVars,
		&db.PatternVar{Pattern: "build/net/%.o", Name: "CFLAGS", Op: vars.OpAppend, Value: "-DNET"},
		&db.PatternVar{Pattern: "build/%.o", Name: "CFLAGS", Op: vars.OpAppend, Value: "-fPIC"},
	)
	n := e.node(d.Enter("build/net/sock.o"))
	if got := x.Value("CFLAGS", e.scope(n)); got != "-O2 -fPIC -DNET" {
		t.Fatalf("CFLAGS = %q, want %q", got, "-O2 -fPIC -DNET")
	}
}

func TestCandidatesSortByFullStem(t *testing.T) {
	e, d, _ := testEngine()
	generic := &db.PatternRule{Targets: []string{"%.o"}}
	specific := &db.PatternRule{Targets: []string{"lib/%.o"}}
	d.PatternRules = []*db.PatternRule{generic, specific}
	got := e.candidates("lib/a.o", nil)
	if len(got) != 2 || got[0].rule != specific || got[1].rule != generic {
		t.Fatalf("candidate order = %#v, want specific then generic", got)
	}
	if got[1].fullStem() != "lib/a" {
		t.Fatalf("generic full stem = %q, want lib/a", got[1].fullStem())
	}
}

func TestDirectoryRelativePrerequisites(t *testing.T) {
	e, _, _ := testEngine()
	c := candidate{
		rule: &db.PatternRule{Prereqs: db.Prereqs{
			Normal:    []string{"%.c", "config.h"},
			OrderOnly: []string{"dirs/%", "generated.h"},
		}},
		dir: "net/", stem: "sock",
	}
	normal, order := e.prereqs(c, "net/sock.o", nil)
	if want := []string{"net/sock.c", "config.h"}; !reflect.DeepEqual(normal, want) {
		t.Fatalf("normal prerequisites = %q, want %q", normal, want)
	}
	if want := []string{"net/dirs/sock", "generated.h"}; !reflect.DeepEqual(order, want) {
		t.Fatalf("order-only prerequisites = %q, want %q", order, want)
	}
}

func TestOughtToExistIncludesKnownPrerequisites(t *testing.T) {
	e, d, _ := testEngine()
	if e.oughtToExist("missing") {
		t.Fatal("unknown missing file ought not exist")
	}

	// Parser mentions and prerequisites accepted by earlier implicit searches
	// are both represented by entries in the rule database, even when they
	// have no rule of their own.
	d.Enter("missing")
	if !e.oughtToExist("missing") {
		t.Fatal("known prerequisite should ought to exist")
	}
}
