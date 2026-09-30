package expand

import (
	"testing"

	"brickmake/internal/diag"
	"brickmake/internal/vars"
)

func newX(defs ...string) *Expander {
	x := New(vars.NewSet())
	for i := 0; i+1 < len(defs); i += 2 {
		x.DefineGlobal(defs[i], vars.OpRecursive, defs[i+1], vars.File, diag.Pos{File: "Makefile", Line: i/2 + 1})
	}
	return x
}

func TestReferences(t *testing.T) {
	x := newX("SRCS", "a.c b.c", "KIND", "SRC", "SRC_LIST", "$(SRCS)", "D", "$$HOME")
	cases := map[string]string{
		"$(SRCS)":             "a.c b.c",
		"${SRCS}":             "a.c b.c",
		"$($(KIND)_LIST)":     "a.c b.c",
		"$(SRCS:.c=.o)":       "a.o b.o",
		"$(SRCS:%.c=obj/%.o)": "obj/a.o obj/b.o",
		"$(D)":                "$HOME",
		"$(NOPE)x":            "x",
		"100$$":               "100$",
	}
	for in, want := range cases {
		if got := x.Expand(in, nil); got != want {
			t.Errorf("Expand(%q) = %q; want %q", in, got, want)
		}
	}
}

func TestFunctions(t *testing.T) {
	x := newX("L", "b a c a", "up", "$(subst a,A,$(1))", "wrap", "[$(1)]")
	cases := map[string]string{
		"$(sort $(L))":                           "a b c",
		"$(words $(L))":                          "4",
		"$(word 2,$(L))":                         "a",
		"$(wordlist 2,3,$(L))":                   "a c",
		"$(filter a c,$(L))":                     "a c a",
		"$(filter-out a,$(L))":                   "b c",
		"$(call up,banana)":                      "bAnAnA",
		"$(foreach w,x y,$(call wrap,$(w)))":     "[x] [y]",
		"$(if ,yes,no)":                          "no",
		"$(or ,,z)":                              "z",
		"$(and a,,b)":                            "",
		"$(join a b,1 2 3)":                      "a1 b2 3",
		"$(addprefix -I,inc src)":                "-Iinc -Isrc",
		"$(dir a.o lib/b.o)":                     "./ lib/",
		"$(notdir lib/b.o)":                      "b.o",
		"$(basename a.c dir.x/y)":                "a dir.x/y",
		"$(subst a,b,x,y)":                       "x,y",
		"$(strip   a   b  )":                     "a b",
		"$(origin L) $(origin NOPE)":             "file undefined",
		"$(flavor L)":                            "recursive",
		"$(value up)":                            "$(subst a,A,$(1))",
		"$(findstring ab,xaby)$(findstring q,x)": "ab",
	}
	for in, want := range cases {
		if got := x.Expand(in, nil); got != want {
			t.Errorf("Expand(%q) = %q; want %q", in, got, want)
		}
	}
}

func TestAutomatic(t *testing.T) {
	x := newX()
	sc := &Scope{Auto: &Auto{Target: "lib/a.o", First: "lib/a.c", Plus: []string{"lib/a.c", "h.h", "h.h"}, All: []string{"lib/a.c", "h.h"}, Stem: "lib/a"}}
	cases := map[string]string{
		"$@ $< $^ $+": "lib/a.o lib/a.c lib/a.c h.h lib/a.c h.h h.h",
		"$(@D) $(@F)": "lib a.o",
		"$(^D)":       "lib .",
		"$*":          "lib/a",
		"$(origin @)": "automatic",
	}
	for in, want := range cases {
		if got := x.Expand(in, sc); got != want {
			t.Errorf("Expand(%q) = %q; want %q", in, got, want)
		}
	}
}

func TestSelfReference(t *testing.T) {
	x := newX("A", "$(A) x")
	defer func() {
		f, ok := recover().(diag.Fatal)
		if !ok || f.Error() != "Makefile:1: *** Recursive variable 'A' references itself (eventually).  Stop." {
			t.Errorf("recover = %v", f)
		}
	}()
	x.Expand("$(A)", nil)
}
