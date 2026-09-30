package glob

import "testing"

func TestMatch(t *testing.T) {
	cases := []struct {
		pattern, name string
		want          bool
	}{
		{"/p/**/*.go", "/p/x/y/a.go", true},
		{"/p/*.go", "/p/x/a.go", false},
		{"/p/a?c", "/p/abc", true},
		{"/p/a?c", "/p/a/c", false},
		{"/p/{a,b}.txt", "/p/b.txt", true},
		{"/p/{a,b}.txt", "/p/c.txt", false},
		{"/p/{a,{b,c}}", "/p/c", true},
		{"/p/[a-c]x", "/p/bx", true},
		{"/p/f{1..3}", "/p/f2", true},
		{"/p/f{1..3}", "/p/f4", false},
		{"/p/f{1..3}", "/p/f02", false},
		{"/p/x{}", "/p/x{}", true},
		{"/p/a,b", "/p/a,b", true},
		{"/p/{a", "/p/{a", true},
		{"/p/\\*", "/p/*", true},
		{"/p/[abc", "/p/[abc", false},
	}
	for _, c := range cases {
		if got := Match(c.pattern, c.name); got != c.want {
			t.Errorf("Match(%q, %q) = %v, want %v", c.pattern, c.name, got, c.want)
		}
	}
}

func TestEscapeDirStar(t *testing.T) {
	dir := EscapeDir("/srv/a*b")
	if !Match(dir+"/x", "/srv/a*b/x") || Match(dir+"/x", "/srv/aZZb/x") {
		t.Errorf("escaped %q", dir)
	}
}
