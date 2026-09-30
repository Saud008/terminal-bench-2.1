package semver

import "testing"

func TestParseRoundTrip(t *testing.T) {
	for _, s := range []string{
		"0.0.0",
		"1.2.3",
		"10.20.30",
		"1.0.0-alpha",
		"1.0.0-alpha.beta.1",
		"1.0.0-x-y-z.--",
		"1.0.0+20130313144700",
		"1.0.0-rc.1+build.7.sha-5114f85",
	} {
		v, err := Parse(s)
		if err != nil {
			t.Fatalf("Parse(%q): %v", s, err)
		}
		if got := v.String(); got != s {
			t.Errorf("Parse(%q).String() = %q", s, got)
		}
	}
}

func TestParseLeadingV(t *testing.T) {
	v, err := Parse("v4.1.0")
	if err != nil || v.String() != "4.1.0" {
		t.Fatalf("Parse(v4.1.0) = %v, %v", v, err)
	}
}

func TestParseRejects(t *testing.T) {
	for _, s := range []string{"", "1", "1.2", "1.2.3.4", "01.2.3", "1.2.3-", "1.2.3+", "1.2.3-a..b", "a.b.c", "1.2.3-a_b"} {
		if _, err := Parse(s); err == nil {
			t.Errorf("Parse(%q) accepted", s)
		}
	}
}

func TestCompareReleases(t *testing.T) {
	order := []string{"0.0.1", "0.1.0", "0.9.9", "1.0.0", "1.0.10", "1.2.0", "2.0.0", "10.0.0"}
	for i := 1; i < len(order); i++ {
		a, b := MustParse(order[i-1]), MustParse(order[i])
		if Compare(a, b) != -1 || Compare(b, a) != 1 {
			t.Errorf("expected %s < %s", a, b)
		}
	}
}

func TestPrereleaseBelowRelease(t *testing.T) {
	if Compare(MustParse("1.0.0-rc.1"), MustParse("1.0.0")) != -1 {
		t.Fatal("1.0.0-rc.1 should sort below 1.0.0")
	}
	if Compare(MustParse("1.0.0-alpha"), MustParse("1.0.0-beta")) != -1 {
		t.Fatal("alpha should sort below beta")
	}
}

func TestBuildIgnored(t *testing.T) {
	if Compare(MustParse("1.0.0+a"), MustParse("1.0.0+b")) != 0 {
		t.Fatal("build metadata must not affect precedence")
	}
	if MustParse("1.0.0+a").Equal(MustParse("1.0.0+b")) {
		t.Fatal("Equal must see build metadata")
	}
}
