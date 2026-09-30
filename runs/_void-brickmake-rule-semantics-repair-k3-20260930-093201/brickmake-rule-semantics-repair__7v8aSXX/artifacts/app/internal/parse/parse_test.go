package parse

import (
	"strings"
	"testing"

	"brickmake/internal/db"
	"brickmake/internal/expand"
	"brickmake/internal/vars"
)

func read(t *testing.T, src string) (*db.DB, *expand.Expander) {
	t.Helper()
	d := db.New()
	x := expand.New(vars.NewSet())
	New(d, x).Parse("Makefile", []byte(src))
	return d, x
}

func TestRulesAndRecipes(t *testing.T) {
	d, x := read(t, "OBJS = a.o b.o\n"+
		"app: $(OBJS) | out\n"+
		"\tcc -o $@ $^ \\\n"+
		"\t  -lm\n"+
		"# comment keeps the rule open\n"+
		"\n"+
		"\t@echo done\n"+
		"out: ; mkdir out\n")
	app := d.Lookup("app")
	if app == nil || len(app.Rules) != 1 {
		t.Fatalf("app rules = %+v", app)
	}
	r := app.Rules[0]
	if strings.Join(r.Normal, " ") != "a.o b.o" || strings.Join(r.OrderOnly, " ") != "out" {
		t.Errorf("prereqs = %v | %v", r.Normal, r.OrderOnly)
	}
	want := []string{"cc -o $@ $^ \\\n  -lm", "@echo done"}
	if r.Recipe == nil || strings.Join(r.Recipe.Lines, "|") != strings.Join(want, "|") {
		t.Errorf("recipe = %q", r.Recipe.Lines)
	}
	if got := d.Lookup("out").Rules[0].Recipe.Lines; len(got) != 1 || got[0] != " mkdir out" {
		t.Errorf("semicolon recipe = %q", got)
	}
	if got := x.Value(".DEFAULT_GOAL", nil); got != "app" {
		t.Errorf("default goal = %q", got)
	}
}

func TestAssignmentsAndComments(t *testing.T) {
	_, x := read(t, "DIR = out # where\nHASH = a\\#b\nS := [$(DIR)]\nC ?= c\nC ?= d\nLIST = a \\\n     b\n")
	cases := map[string]string{"DIR": "out ", "HASH": "a#b", "S": "[out ]", "C": "c", "LIST": "a b"}
	for name, want := range cases {
		if got := x.Value(name, nil); got != want {
			t.Errorf("%s = %q; want %q", name, got, want)
		}
	}
}

func TestConditionals(t *testing.T) {
	_, x := read(t, `E =
R = $(E)
ifdef E
A += E
endif
ifdef R
A += R
endif
ifeq ($(R),)
A += empty
else
A += nonempty
endif
ifneq "a" 'a'
A += bad
else ifeq (x,x)
A += elseif
endif
ifeq ( a , a )
A += spaces
endif
`)
	if got := x.Value("A", nil); got != "R empty elseif" {
		t.Errorf("A = %q", got)
	}
}

func TestPatternRulesAndStatic(t *testing.T) {
	d, _ := read(t, "%.o: %.c\n\tcc $<\n%.o: %.s\n\tas $<\n%.o: %.c\n\tcc2 $<\n"+
		"OBJS := x.o y.o\n$(OBJS): %.o: src/%.c\n\t@echo $@\n")
	if n := len(d.PatternRules); n != 2 {
		t.Fatalf("pattern rules = %d", n)
	}
	if got := d.PatternRules[1].Recipe.Lines[0]; got != "cc2 $<" {
		t.Errorf("redefined rule should move last, got %q", got)
	}
	y := d.Lookup("y.o").Rules[0]
	if !y.Static || y.Stem != "y" || strings.Join(y.Normal, " ") != "src/y.c" {
		t.Errorf("static rule = %+v", y)
	}
}

func TestTargetAndPatternVars(t *testing.T) {
	d, _ := read(t, "t: V = a;b\n%.o: CF += -g\n")
	if v := d.Lookup("t").Vars.Get("V"); v == nil || v.Value != "a;b" {
		t.Errorf("t: V = %+v", v)
	}
	if len(d.PatternVars) != 1 || d.PatternVars[0].Pattern != "%.o" || d.PatternVars[0].Op != vars.OpAppend {
		t.Errorf("pattern vars = %+v", d.PatternVars)
	}
}
