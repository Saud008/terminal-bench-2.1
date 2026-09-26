package engine

import (
	"testing"

	"brickmake/internal/db"
)

func TestPrefixes(t *testing.T) {
	cases := []struct {
		in, text              string
		silent, ignore, force bool
	}{
		{"echo hi", "echo hi", false, false, false},
		{"@echo hi", "echo hi", true, false, false},
		{"-@ echo hi", "echo hi", true, true, false},
		{"+@echo hi", "echo hi", true, false, true},
		{"  \t@-+rm x", "rm x", true, true, true},
		{"echo -@", "echo -@", false, false, false},
	}
	for _, c := range cases {
		var cmd command
		got := prefixes(c.in, &cmd)
		if got != c.text || cmd.silent != c.silent || cmd.ignore != c.ignore || cmd.force != c.force {
			t.Errorf("prefixes(%q) = %q %+v", c.in, got, cmd)
		}
	}
}

func TestAllForced(t *testing.T) {
	if allForced(&db.Recipe{Lines: []string{"+touch a", "@+echo b"}}) != true {
		t.Error("all + lines should be forced")
	}
	if allForced(&db.Recipe{Lines: []string{"+touch a", "echo b"}}) {
		t.Error("mixed recipe is not forced")
	}
	if allForced(nil) {
		t.Error("nil recipe is not forced")
	}
}
