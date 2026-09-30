package db

import "testing"

func TestPatternRuleIdentityIncludesOrderOnlyPrerequisites(t *testing.T) {
	d := New()
	a := &PatternRule{Targets: []string{"%.o"}, Prereqs: Prereqs{Normal: []string{"%.c"}, OrderOnly: []string{"a"}}, Recipe: &Recipe{}}
	b := &PatternRule{Targets: []string{"%.o"}, Prereqs: Prereqs{Normal: []string{"%.c"}, OrderOnly: []string{"b"}}, Recipe: &Recipe{}}
	d.AddPatternRule(a)
	d.AddPatternRule(b)
	if len(d.PatternRules) != 2 {
		t.Fatalf("rules = %d, want 2", len(d.PatternRules))
	}
}
