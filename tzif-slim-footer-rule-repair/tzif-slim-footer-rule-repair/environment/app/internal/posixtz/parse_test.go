package posixtz

import "testing"

func TestParseUS(t *testing.T) {
	tz, err := Parse("EST5EDT,M3.2.0,M11.1.0")
	if err != nil {
		t.Fatal(err)
	}
	if tz.Std != "EST" || tz.StdOffset != -5*3600 || tz.Dst != "EDT" || tz.DstOffset != -4*3600 {
		t.Fatalf("zones: %+v", tz)
	}
	want := Rule{Kind: MonthWeekDay, Month: 3, Week: 2, Weekday: 0, Time: 7200}
	if tz.Start != want {
		t.Fatalf("start = %+v, want %+v", tz.Start, want)
	}
}

func TestParseQuotedNoDST(t *testing.T) {
	tz, err := Parse("<+0330>-3:30")
	if err != nil {
		t.Fatal(err)
	}
	if tz.HasDST || tz.Std != "+0330" || tz.StdOffset != 3*3600+30*60 {
		t.Fatalf("got %+v", tz)
	}
}

func TestParseRejectsGarbage(t *testing.T) {
	for _, s := range []string{"", "E5", "EST5EDT,M13.1.0,M11.1.0", "EST5EDT,M3.2.0"} {
		if _, err := Parse(s); err == nil {
			t.Errorf("Parse(%q) succeeded", s)
		}
	}
}
