package text

import "testing"

func TestMatch(t *testing.T) {
	cases := []struct {
		pat, s, stem string
		ok           bool
	}{
		{"%.o", "a.o", "a", true},
		{"%.o", "lib/a.o", "lib/a", true},
		{"lib/%.o", "lib/a.o", "a", true},
		{"%.o", ".o", "", true},
		{"a%b", "ab", "", true},
		{"a%b", "acb", "c", true},
		{"%.o", "a.c", "", false},
		{"x.o", "x.o", "", true},
		{"x.o", "y.o", "", false},
	}
	for _, c := range cases {
		stem, ok := Match(c.pat, c.s)
		if stem != c.stem || ok != c.ok {
			t.Errorf("Match(%q, %q) = %q, %v; want %q, %v", c.pat, c.s, stem, ok, c.stem, c.ok)
		}
	}
}

func TestPatsubst(t *testing.T) {
	cases := []struct{ pat, repl, in, want string }{
		{"%.c", "%.o", "a.c b.c  c.h", "a.o b.o c.h"},
		{"%.c", "obj/%.o", "src/a.c", "obj/src/a.o"},
		{"a.c", "x", "a.c b.c", "x b.c"},
		{"%", "[%]", "a b", "[a] [b]"},
	}
	for _, c := range cases {
		if got := Patsubst(c.pat, c.repl, c.in); got != c.want {
			t.Errorf("Patsubst(%q, %q, %q) = %q; want %q", c.pat, c.repl, c.in, got, c.want)
		}
	}
}

func TestFileNames(t *testing.T) {
	if got := Dir("a.o"); got != "./" {
		t.Errorf("Dir(a.o) = %q", got)
	}
	if got := Dir("lib/x/a.o"); got != "lib/x/" {
		t.Errorf("Dir = %q", got)
	}
	if got := Suffix("dir.x/y"); got != "" {
		t.Errorf("Suffix(dir.x/y) = %q", got)
	}
	if got := Basename("dir/a.tar.gz"); got != "dir/a.tar" {
		t.Errorf("Basename = %q", got)
	}
}

func TestSplitOrder(t *testing.T) {
	n, o := SplitOrder([]string{"a", "b", "|", "c", "|", "d"})
	if Join(n) != "a b" || Join(o) != "c d" {
		t.Errorf("SplitOrder = %v | %v", n, o)
	}
	n, o = SplitOrder([]string{"a"})
	if Join(n) != "a" || o != nil {
		t.Errorf("SplitOrder = %v | %v", n, o)
	}
}
