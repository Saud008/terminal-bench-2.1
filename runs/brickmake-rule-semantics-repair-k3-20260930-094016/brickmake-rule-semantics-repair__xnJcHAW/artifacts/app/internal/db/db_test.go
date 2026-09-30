package db

import "testing"

func TestPatternRuleIdentityIncludesOrderOnlyPrerequisites(t *testing.T) {
	d := New()
	a := &PatternRule{Targets: []string{"%.o"}, Prereqs: Prereqs{Normal: []string{"%.c"}, OrderOnly: []string{"one"}}, Recipe: &Recipe{}}
	b := &PatternRule{Targets: []string{"%.o"}, Prereqs: Prereqs{Normal: []string{"%.c"}, OrderOnly: []string{"two"}}, Recipe: &Recipe{}}
	d.AddPatternRule(a)
	d.AddPatternRule(b)
	if len(d.PatternRules) != 2 {
		t.Fatalf("got %d pattern rules, want 2", len(d.PatternRules))
	}
}

func TestPatternRuleIdentityIncludesSecondaryExpansionMode(t *testing.T) {
	d := New()
	a := &PatternRule{Targets: []string{"%.o"}, Prereqs: Prereqs{Normal: []string{"x"}}, Recipe: &Recipe{}}
	b := &PatternRule{Targets: []string{"%.o"}, Prereqs: Prereqs{Second: true, Text: "x"}, Recipe: &Recipe{}}
	d.AddPatternRule(a)
	d.AddPatternRule(b)
	if len(d.PatternRules) != 2 {
		t.Fatalf("got %d pattern rules, want 2", len(d.PatternRules))
	}
}

func TestIdenticalPatternRuleStillReplaces(t *testing.T) {
	d := New()
	a := &PatternRule{Targets: []string{"%.o"}, Prereqs: Prereqs{Normal: []string{"%.c"}, OrderOnly: []string{"dir"}}, Recipe: &Recipe{}}
	b := &PatternRule{Targets: []string{"%.o"}, Prereqs: Prereqs{Normal: []string{"%.c"}, OrderOnly: []string{"dir"}}, Recipe: &Recipe{}}
	d.AddPatternRule(a)
	d.AddPatternRule(b)
	if len(d.PatternRules) != 1 || d.PatternRules[0] != b {
		t.Fatal("identical rule was not replaced")
	}
}
