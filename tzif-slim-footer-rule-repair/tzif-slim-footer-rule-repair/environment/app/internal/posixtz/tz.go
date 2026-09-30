// Package posixtz parses and evaluates the POSIX TZ strings found in the
// footer of version 2+ TZif files (RFC 8536 section 3.3).
package posixtz

// RuleKind selects how a Rule names its day.
type RuleKind int

const (
	// JulianNoLeap is the "Jn" form.
	JulianNoLeap RuleKind = iota
	// ZeroBased is the bare "n" form.
	ZeroBased
	// MonthWeekDay is the "Mm.w.d" form.
	MonthWeekDay
)

// Rule is one of the two date/time pairs that bound daylight saving time.
type Rule struct {
	Kind    RuleKind
	Day     int // JulianNoLeap and ZeroBased
	Month   int // MonthWeekDay: 1-12
	Week    int // MonthWeekDay: 1-5
	Weekday int // MonthWeekDay: 0 (Sunday) - 6
	// Time is the local wall-clock time of the transition, in seconds after
	// midnight of the rule's day.
	Time int64
}

// Zone is a resolved local time type.
type Zone struct {
	Offset int64 // seconds east of UTC
	Abbr   string
	IsDST  bool
}

// Transition is a change of local time type at a UTC instant.
type Transition struct {
	At   int64
	Zone Zone
}

// TZ is a parsed POSIX TZ string.
type TZ struct {
	Raw       string
	Std       string
	StdOffset int64 // seconds east of UTC
	Dst       string
	DstOffset int64
	HasDST    bool
	Start     Rule // transition into daylight saving time
	End       Rule // transition back to standard time
}

func (tz *TZ) stdZone() Zone { return Zone{Offset: tz.StdOffset, Abbr: tz.Std} }

func (tz *TZ) dstZone() Zone { return Zone{Offset: tz.DstOffset, Abbr: tz.Dst, IsDST: true} }
