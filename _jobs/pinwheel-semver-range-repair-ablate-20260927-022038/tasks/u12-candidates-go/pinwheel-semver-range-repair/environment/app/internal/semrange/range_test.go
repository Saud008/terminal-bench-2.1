package semrange

import (
	"testing"

	"github.com/brightloom/pinwheel/internal/semver"
)

func TestSatisfies(t *testing.T) {
	cases := []struct {
		version, rng string
		want         bool
	}{
		{"1.5.0", "^1.2.3", true},
		{"2.0.0", "^1.2.3", false},
		{"1.2.2", "^1.2.3", false},
		{"1.2.9", "~1.2.3", true},
		{"1.3.0", "~1.2.3", false},
		{"1.9.3", "1.x", true},
		{"2.0.0", "1.x", false},
		{"1.4.0", ">=1.0.0 <2.0.0", true},
		{"2.0.0", ">=1.0.0 <2.0.0", false},
		{"2.3.4", "1.2.3 - 2.3.4", true},
		{"2.3.5", "1.2.3 - 2.3.4", false},
		{"3.1.0", "^1.0.0 || ^3.0.0", true},
		{"2.1.0", "^1.0.0 || ^3.0.0", false},
		{"0.0.1", "*", true},
		{"1.2.3", "1.2.3", true},
		{"1.2.4", "1.2.3", false},
		{"1.0.0-rc.2", ">=1.0.0-rc.1", true},
	}
	for _, c := range cases {
		r, err := Parse(c.rng)
		if err != nil {
			t.Fatalf("Parse(%q): %v", c.rng, err)
		}
		if got := r.Test(semver.MustParse(c.version)); got != c.want {
			t.Errorf("%s satisfies %q = %v, want %v", c.version, c.rng, got, c.want)
		}
	}
}

func TestParseRejects(t *testing.T) {
	for _, s := range []string{"1.2.3.4", ">=abc", "^1.2.3 || foo", "1.2.3 -", "~>"} {
		if _, err := Parse(s); err == nil {
			t.Errorf("Parse(%q) accepted", s)
		}
	}
}
