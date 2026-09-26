package civil

import "testing"

func TestRoundTrip(t *testing.T) {
	for _, days := range []int64{-719468, -1, 0, 1, 11016, 25567, 47482, 2932896} {
		y, m, d := CivilFromDays(days)
		if got := DaysFromCivil(y, m, d); got != days {
			t.Fatalf("round trip %d -> %04d-%02d-%02d -> %d", days, y, m, d, got)
		}
	}
}

func TestWeekday(t *testing.T) {
	if w := Weekday(DaysFromCivil(2000, 1, 1)); w != 6 {
		t.Fatalf("2000-01-01 weekday = %d, want 6 (Saturday)", w)
	}
	if w := Weekday(DaysFromCivil(1969, 12, 31)); w != 3 {
		t.Fatalf("1969-12-31 weekday = %d, want 3 (Wednesday)", w)
	}
}

func TestParseInstant(t *testing.T) {
	got, err := ParseInstant("2038-01-19T03:14:08Z")
	if err != nil || got != 1<<31 {
		t.Fatalf("ParseInstant = %d, %v", got, err)
	}
	if _, err := ParseInstant("2038-02-30T00:00:00Z"); err == nil {
		t.Fatal("expected error for February 30")
	}
}
