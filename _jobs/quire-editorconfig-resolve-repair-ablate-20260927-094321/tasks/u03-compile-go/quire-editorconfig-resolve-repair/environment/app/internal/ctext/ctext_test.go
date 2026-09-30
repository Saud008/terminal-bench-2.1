package ctext

import "testing"

func TestAtoi(t *testing.T) {
	for in, want := range map[string]int{
		"12":    12,
		" -7x":  -7,
		"+3..5": 3,
		"":      0,
		"abc":   0,
		"08":    8,
	} {
		if got := Atoi(in); got != want {
			t.Errorf("Atoi(%q) = %d, want %d", in, got, want)
		}
	}
}

func TestLowerIsASCIIOnly(t *testing.T) {
	if got := Lower("UTF-8 ÄB"); got != "utf-8 Äb" {
		t.Errorf("Lower = %q", got)
	}
	if !EqualFold("ROOT", "root") || EqualFold("root", "roots") {
		t.Error("EqualFold")
	}
}

func TestTrim(t *testing.T) {
	if got := TrimLeft(TrimRight(" \t a b \r\n")); got != "a b" {
		t.Errorf("trim = %q", got)
	}
}
