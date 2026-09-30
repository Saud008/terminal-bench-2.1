package engine

import (
	"reflect"
	"testing"

	"brickmake/internal/db"
	"brickmake/internal/diag"
	"brickmake/internal/expand"
	"brickmake/internal/vars"
)

func patternEngine() (*Engine, *db.DB, *expand.Expander) {
	d := db.New()
	x := expand.New(vars.NewSet())
	return New(d, x), d, x
}

func TestPatternVariablesSpecificity(t *testing.T) {
	e, d, x := patternEngine()
	x.DefineGlobal("CFLAGS", vars.OpRecursive, "-O2", vars.File, diag.Pos{})
	// Deliberately define the more specific pattern first.
	d.PatternVars = append(d.PatternVars,
		&db.PatternVar{Pattern: "build/net/%.o", Name: "CFLAGS", Op: vars.OpAppend, Value: "-DNET"},
		&db.PatternVar{Pattern: "build/%.o", Name: "CFLAGS", Op: vars.OpAppend, Value: "-fPIC"},
	)
	n := e.node(d.Enter("build/net/sock.o"))
	if got := x.Value("CFLAGS", e.scope(n)); got != "-O2 -fPIC -DNET" {
		t.Fatalf("CFLAGS = %q", got)
	}
}

func TestImplicitCandidatesUseFullStem(t *testing.T) {
	e, d, _ := patternEngine()
	generic := &db.PatternRule{Targets: []string{"%.o"}, Prereqs: db.Prereqs{Normal: []string{"%.s"}}}
	specific := &db.PatternRule{Targets: []string{"lib/%.o"}, Prereqs: db.Prereqs{Normal: []string{"lib/%.c"}}}
	d.PatternRules = []*db.PatternRule{generic, specific}
	cs := e.candidates("lib/a.o", map[*db.PatternRule]bool{})
	if len(cs) != 2 || cs[0].rule != specific || cs[0].fullStem() != "a" || cs[1].fullStem() != "lib/a" {
		t.Fatalf("candidates = %#v", cs)
	}
}

func TestImplicitDirectoryOnlyPrefixesPercentPrerequisites(t *testing.T) {
	e, d, _ := patternEngine()
	r := &db.PatternRule{Targets: []string{"%.o"}, Prereqs: db.Prereqs{
		Normal: []string{"%.c", "config.h"}, OrderOnly: []string{"%/dir", "generated.h"},
	}}
	d.PatternRules = []*db.PatternRule{r}
	c := e.candidates("net/sock.o", nil)[0]
	n, o := e.prereqs(c, "net/sock.o", nil)
	if !reflect.DeepEqual(n, []string{"net/sock.c", "config.h"}) ||
		!reflect.DeepEqual(o, []string{"net/sock/dir", "generated.h"}) {
		t.Fatalf("normal=%v order-only=%v", n, o)
	}
}

func TestExplicitPrerequisiteOughtToExist(t *testing.T) {
	e, d, _ := patternEngine()
	d.Enter("mentioned.h") // parser enters explicit prerequisites even without a rule
	if !e.oughtToExist("mentioned.h") {
		t.Fatal("explicitly mentioned prerequisite should ought to exist")
	}
	if e.oughtToExist("unknown.h") {
		t.Fatal("unknown missing file should not ought to exist")
	}
}

func TestSecondaryImplicitDirectoryPrefix(t *testing.T) {
	e, d, _ := patternEngine()
	r := &db.PatternRule{Targets: []string{"%.o"}, Prereqs: db.Prereqs{
		Text: "$(DEP) fixed.h", Second: true,
	}}
	d.PatternRules = []*db.PatternRule{r}
	sc := &expand.Scope{Sets: []*vars.Set{vars.NewSet()}}
	sc.Sets[0].Put(&vars.Var{Name: "DEP", Value: "%.c", Flavor: vars.Recursive})
	c := e.candidates("net/sock.o", nil)[0]
	n, _ := e.prereqs(c, "net/sock.o", sc)
	if !reflect.DeepEqual(n, []string{"net/sock.c", "fixed.h"}) {
		t.Fatalf("normal = %v", n)
	}
}
