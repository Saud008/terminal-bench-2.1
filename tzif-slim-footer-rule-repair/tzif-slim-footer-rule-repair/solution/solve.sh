#!/usr/bin/env bash
set -euo pipefail

cd /app

# Rule times: RFC 8536 3.3.1 lets the hour be signed and run to 167
# (America/Nuuk "/-1", Asia/Jerusalem "/26"); a bad value is an error, not 02:00.
cat > internal/posixtz/hms.go <<'EOF'
package posixtz

import (
	"fmt"
	"strconv"
	"strings"
)

// parseHMS parses [+-]hh[:mm[:ss]] into seconds. maxHour bounds the hour
// field; signed controls whether a leading sign is accepted.
func parseHMS(s string, maxHour int, signed bool) (int64, error) {
	neg := false
	if signed && s != "" && (s[0] == '+' || s[0] == '-') {
		neg = s[0] == '-'
		s = s[1:]
	}
	parts := strings.Split(s, ":")
	if s == "" || len(parts) > 3 {
		return 0, fmt.Errorf("malformed %q", s)
	}
	var total int64
	for i, part := range parts {
		if part == "" || len(part) > 3 || (i > 0 && len(part) != 2) || strings.Trim(part, "0123456789") != "" {
			return 0, fmt.Errorf("malformed %q", s)
		}
		n, err := strconv.Atoi(part)
		if err != nil {
			return 0, fmt.Errorf("malformed %q", s)
		}
		switch i {
		case 0:
			if n > maxHour {
				return 0, fmt.Errorf("hour %d out of range", n)
			}
			total += int64(n) * 3600
		default:
			if n > 59 {
				return 0, fmt.Errorf("field %d out of range", n)
			}
			if i == 1 {
				total += int64(n) * 60
			} else {
				total += int64(n)
			}
		}
	}
	if neg {
		total = -total
	}
	return total, nil
}

// parseRuleTime parses the "/time" part of a rule. RFC 8536 section 3.3.1
// extends POSIX here: the hour may be signed and range from -167 to 167.
func parseRuleTime(s string) (int64, error) {
	return parseHMS(s, 167, true)
}
EOF

# Day selection: "Jn" never counts February 29, so from J60 on it shifts by one
# day in leap years; "Mm.5.d" is the last d of the month, not a fifth week.
cat > internal/posixtz/rule.go <<'EOF'
package posixtz

import "shiftclock/internal/civil"

// yearDay returns the zero-based day of year (0 = January 1) that r names in
// year y.
func (r Rule) yearDay(y int64) int {
	switch r.Kind {
	case JulianNoLeap:
		d := r.Day - 1
		if r.Day >= 60 && civil.IsLeap(y) {
			d++
		}
		return d
	case ZeroBased:
		return r.Day
	default:
		first := civil.DaysFromCivil(y, r.Month, 1)
		day := 1 + (r.Weekday-civil.Weekday(first)+7)%7 + (r.Week-1)*7
		if day > civil.DaysInMonth(y, r.Month) {
			day -= 7
		}
		return int(first - civil.DaysFromCivil(y, 1, 1) + int64(day-1))
	}
}

// Instant returns the UTC time of the transition r names in year y, given
// the UTC offset in effect just before the transition.
func (r Rule) Instant(y int64, before int64) int64 {
	days := civil.DaysFromCivil(y, 1, 1) + int64(r.yearDay(y))
	return days*civil.SecondsPerDay + r.Time - before
}
EOF

# Evaluation: the end rule is wall time under the DST offset, and DST may wrap
# the year (southern hemisphere, Europe/Dublin), so resolve t against the
# chronologically ordered transitions of the neighbouring years.
cat > internal/posixtz/eval.go <<'EOF'
package posixtz

import (
	"sort"

	"shiftclock/internal/civil"
)

// yearTransitions returns the two transitions whose rules fall in year y,
// in chronological order.
func (tz *TZ) yearTransitions(y int64) [2]Transition {
	start := Transition{At: tz.Start.Instant(y, tz.StdOffset), Zone: tz.dstZone()}
	end := Transition{At: tz.End.Instant(y, tz.DstOffset), Zone: tz.stdZone()}
	if end.At < start.At {
		return [2]Transition{end, start}
	}
	return [2]Transition{start, end}
}

// Lookup returns the local time type in effect at Unix time t.
func (tz *TZ) Lookup(t int64) Zone {
	if !tz.HasDST {
		return tz.stdZone()
	}
	y := civil.YearOf(t)
	var best Transition
	found := false
	for yy := y - 1; yy <= y+1; yy++ {
		for _, tr := range tz.yearTransitions(yy) {
			if tr.At <= t && (!found || tr.At > best.At) {
				best, found = tr, true
			}
		}
	}
	return best.Zone
}

// Transitions returns the rule transitions with from <= At < to, in order.
func (tz *TZ) Transitions(from, to int64) []Transition {
	if !tz.HasDST || from >= to {
		return nil
	}
	var out []Transition
	for y := civil.YearOf(from) - 1; y <= civil.YearOf(to)+1; y++ {
		for _, tr := range tz.yearTransitions(y) {
			if tr.At >= from && tr.At < to {
				out = append(out, tr)
			}
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i].At < out[j].At })
	return out
}
EOF

# Leap-second records (right/ files): parse them in both the 32-bit v1 block and
# the 64-bit block, and map instants of the file's leap-counting scale to UTC
# readings and back. The footer's rules are in UTC, so they see readings.
cat > internal/tzif/leap.go <<'EOF'
package tzif

import "sort"

// Leap is one leap-second record: from instant At on, a total correction of
// Corr seconds is in effect.
type Leap struct {
	At   int64
	Corr int64
}

func (f *File) prevCorr(i int) int64 {
	if i == 0 {
		return 0
	}
	return f.Leaps[i-1].Corr
}

// UTC maps instant t of the file's time scale to POSIX seconds. In a file
// with leap-second records instants count leap seconds; leap reports that t
// is an inserted leap second, and posix is then the second before it.
func (f *File) UTC(t int64) (posix int64, leap bool) {
	i := sort.Search(len(f.Leaps), func(i int) bool { return f.Leaps[i].At > t }) - 1
	if i < 0 {
		return t, false
	}
	l := f.Leaps[i]
	return t - l.Corr, t == l.At && l.Corr > f.prevCorr(i)
}

// Instant is the inverse of UTC: it returns the instant whose UTC reading
// is the POSIX time p, never an inserted leap second.
func (f *File) Instant(p int64) int64 {
	for i := len(f.Leaps) - 1; i >= 0; i-- {
		l := f.Leaps[i]
		t := p + l.Corr
		if t > l.At || t == l.At && l.Corr <= f.prevCorr(i) {
			return t
		}
	}
	return p
}
EOF

cat > internal/tzif/file.go <<'EOF'
package tzif

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"os"

	"shiftclock/internal/posixtz"
)

// LocalType is one ttinfo record.
type LocalType struct {
	Offset int64
	IsDST  bool
	Abbr   string
}

// File is a decoded TZif file. For version 2+ files only the 64-bit data
// block is kept.
type File struct {
	Version int
	Times   []int64 // transition times, ascending
	Indices []uint8
	Types   []LocalType
	Leaps   []Leap // leap-second records, ascending
	Footer  string
	Rule    *posixtz.TZ // nil when the footer is empty
}

// Load reads and parses the TZif file at path.
func Load(path string) (*File, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	f, err := Parse(b)
	if err != nil {
		return nil, fmt.Errorf("%s: %w", path, err)
	}
	return f, nil
}

// Parse decodes a TZif file held in memory.
func Parse(b []byte) (*File, error) {
	h, err := parseHeader(b)
	if err != nil {
		return nil, err
	}
	if h.version == 0 {
		f, _, err := parseBlock(b[headerLen:], h, 4)
		if err != nil {
			return nil, err
		}
		f.Version = 1
		return f, nil
	}

	off := headerLen + h.dataLen(4)
	if len(b) < off {
		return nil, errTruncated("version 1 data block")
	}
	h2, err := parseHeader(b[off:])
	if err != nil {
		return nil, err
	}
	f, n, err := parseBlock(b[off+headerLen:], h2, 8)
	if err != nil {
		return nil, err
	}
	f.Version = int(h2.version - '0')

	rest := b[off+headerLen+n:]
	if len(rest) < 2 || rest[0] != '\n' {
		return nil, errCorrupt("missing footer")
	}
	end := bytes.IndexByte(rest[1:], '\n')
	if end < 0 {
		return nil, errCorrupt("unterminated footer")
	}
	f.Footer = string(rest[1 : 1+end])
	if f.Footer != "" {
		if f.Rule, err = posixtz.Parse(f.Footer); err != nil {
			return nil, err
		}
	}
	return f, nil
}

// parseBlock decodes one data block and returns the number of bytes used.
func parseBlock(b []byte, h header, timeSize int) (*File, int, error) {
	n := h.dataLen(timeSize)
	if len(b) < n {
		return nil, 0, errTruncated("data block")
	}
	f := &File{}
	p := 0
	for i := 0; i < h.timecnt; i++ {
		if timeSize == 4 {
			f.Times = append(f.Times, int64(int32(binary.BigEndian.Uint32(b[p:]))))
		} else {
			f.Times = append(f.Times, int64(binary.BigEndian.Uint64(b[p:])))
		}
		p += timeSize
	}
	for i := 1; i < len(f.Times); i++ {
		if f.Times[i] <= f.Times[i-1] {
			return nil, 0, errCorrupt("transition times not ascending")
		}
	}
	f.Indices = append([]uint8(nil), b[p:p+h.timecnt]...)
	p += h.timecnt
	for _, idx := range f.Indices {
		if int(idx) >= h.typecnt {
			return nil, 0, errCorrupt("transition type index out of range")
		}
	}
	chars := b[p+h.typecnt*6 : p+h.typecnt*6+h.charcnt]
	for i := 0; i < h.typecnt; i++ {
		rec := b[p+6*i:]
		ai := int(rec[5])
		if ai >= len(chars) {
			return nil, 0, errCorrupt("abbreviation index out of range")
		}
		abbr := chars[ai:]
		if z := bytes.IndexByte(abbr, 0); z >= 0 {
			abbr = abbr[:z]
		}
		f.Types = append(f.Types, LocalType{
			Offset: int64(int32(binary.BigEndian.Uint32(rec))),
			IsDST:  rec[4] != 0,
			Abbr:   string(abbr),
		})
	}
	p += h.typecnt*6 + h.charcnt
	for i := 0; i < h.leapcnt; i++ {
		var at int64
		if timeSize == 4 {
			at = int64(int32(binary.BigEndian.Uint32(b[p:])))
		} else {
			at = int64(binary.BigEndian.Uint64(b[p:]))
		}
		corr := int64(int32(binary.BigEndian.Uint32(b[p+timeSize:])))
		p += timeSize + 4
		if i > 0 && at <= f.Leaps[i-1].At {
			return nil, 0, errCorrupt("leap-second records not ascending")
		}
		f.Leaps = append(f.Leaps, Leap{At: at, Corr: corr})
	}
	return f, n, nil
}
EOF

cat > internal/tzif/lookup.go <<'EOF'
package tzif

import (
	"sort"

	"shiftclock/internal/posixtz"
)

func (f *File) zone(i uint8) posixtz.Zone {
	lt := f.Types[i]
	return posixtz.Zone{Offset: lt.Offset, Abbr: lt.Abbr, IsDST: lt.IsDST}
}

// ruleLookup evaluates the footer at instant t. The footer's rules are
// stated in UTC, so t is read through the leap-second records first.
func (f *File) ruleLookup(t int64) posixtz.Zone {
	p, _ := f.UTC(t)
	return f.Rule.Lookup(p)
}

// Lookup returns the local time type in effect at instant t.
//
// Before the first transition the first ttinfo applies. After the last
// transition (or everywhere, for a file without transitions) the footer
// rule applies when there is one; otherwise the last transition's type
// stays in effect.
func (f *File) Lookup(t int64) posixtz.Zone {
	n := len(f.Times)
	if n == 0 {
		if f.Rule != nil {
			return f.ruleLookup(t)
		}
		return f.zone(0)
	}
	if t < f.Times[0] {
		return f.zone(0)
	}
	if t > f.Times[n-1] && f.Rule != nil {
		return f.ruleLookup(t)
	}
	i := sort.Search(n, func(i int) bool { return f.Times[i] > t }) - 1
	return f.zone(f.Indices[i])
}

// Transitions lists the changes of local time type with from <= At < to,
// taken from the transition table and, past its end, from the footer.
// Entries that would not change the offset, abbreviation or DST flag are
// dropped.
func (f *File) Transitions(from, to int64) []posixtz.Transition {
	var all []posixtz.Transition
	for i, at := range f.Times {
		all = append(all, posixtz.Transition{At: at, Zone: f.zone(f.Indices[i])})
	}
	if f.Rule != nil {
		ruleFrom := from
		if n := len(f.Times); n > 0 && f.Times[n-1]+1 > ruleFrom {
			ruleFrom = f.Times[n-1] + 1
		}
		pf, _ := f.UTC(ruleFrom)
		pt, _ := f.UTC(to)
		for _, tr := range f.Rule.Transitions(pf, pt+1) {
			tr.At = f.Instant(tr.At)
			if tr.At >= ruleFrom {
				all = append(all, tr)
			}
		}
	}

	var out []posixtz.Transition
	for _, tr := range all {
		if tr.At >= to {
			break
		}
		if tr.Zone == f.Lookup(tr.At-1) {
			continue
		}
		if tr.At >= from {
			out = append(out, tr)
		}
	}
	return out
}
EOF

# Output and input go through those readings: an inserted leap second reads as
# second 60, RFC 3339 input (second 60 included) and the transitions year
# bounds are mapped back to instants.
cat > internal/civil/format.go <<'EOF'
package civil

import (
	"fmt"
	"strconv"
	"strings"
)

const SecondsPerDay = 86400

// Split breaks a Unix time into a day number and the seconds into that day.
func Split(t int64) (days, sod int64) {
	days = FloorDiv(t, SecondsPerDay)
	return days, t - days*SecondsPerDay
}

// YearOf returns the calendar year containing Unix time t (read as UTC).
func YearOf(t int64) int64 {
	days, _ := Split(t)
	y, _, _ := CivilFromDays(days)
	return y
}

// Format renders t as YYYY-MM-DDTHH:MM:SS with no zone designator.
func Format(t int64) string {
	return FormatLeap(t, false)
}

// FormatLeap is Format for a reading taken during an inserted leap second
// when leap is set: t is then the second before it, and the leap second is
// shown as that second plus one (normally second 60).
func FormatLeap(t int64, leap bool) string {
	days, sod := Split(t)
	y, m, d := CivilFromDays(days)
	sec := sod % 60
	if leap {
		sec++
	}
	return fmt.Sprintf("%04d-%02d-%02dT%02d:%02d:%02d", y, m, d, sod/3600, sod/60%60, sec)
}

// FormatUTC renders t as an RFC 3339 UTC timestamp.
func FormatUTC(t int64) string {
	return Format(t) + "Z"
}

// ParseInstant accepts either a decimal Unix time or YYYY-MM-DDTHH:MM:SSZ.
func ParseInstant(s string) (int64, error) {
	if n, err := strconv.ParseInt(s, 10, 64); err == nil {
		return n, nil
	}
	p, sec60, err := ParseUTC(s)
	if err != nil {
		return 0, err
	}
	if sec60 {
		return 0, fmt.Errorf("instant %q: field out of range", s)
	}
	return p, nil
}

// ParseUTC parses YYYY-MM-DDTHH:MM:SSZ into POSIX seconds. Second 60 is
// accepted: the result is then the time of second 59 and sec60 is set.
func ParseUTC(s string) (p int64, sec60 bool, err error) {
	if !strings.HasSuffix(s, "Z") || len(s) != 20 || s[4] != '-' || s[7] != '-' || s[10] != 'T' || s[13] != ':' || s[16] != ':' {
		return 0, false, fmt.Errorf("instant %q: want Unix seconds or YYYY-MM-DDTHH:MM:SSZ", s)
	}
	var fields [6]int64
	for i, span := range [6][2]int{{0, 4}, {5, 7}, {8, 10}, {11, 13}, {14, 16}, {17, 19}} {
		n, err := strconv.ParseInt(s[span[0]:span[1]], 10, 64)
		if err != nil {
			return 0, false, fmt.Errorf("instant %q: %v", s, err)
		}
		fields[i] = n
	}
	y, mo, d := fields[0], int(fields[1]), int(fields[2])
	if mo < 1 || mo > 12 || d < 1 || d > DaysInMonth(y, mo) || fields[3] > 23 || fields[4] > 59 || fields[5] > 60 {
		return 0, false, fmt.Errorf("instant %q: field out of range", s)
	}
	if fields[5] == 60 {
		sec60 = true
		fields[5] = 59
	}
	return DaysFromCivil(y, mo, d)*SecondsPerDay + fields[3]*3600 + fields[4]*60 + fields[5], sec60, nil
}
EOF

cat > internal/report/json.go <<'EOF'
// Package report renders shiftclock results as one JSON object per line.
// Keys are written in a fixed order so output can be diffed across runs.
package report

import (
	"fmt"
	"io"
	"strconv"

	"shiftclock/internal/civil"
	"shiftclock/internal/posixtz"
)

// Instant writes the local time type in effect at an instant whose UTC
// reading is the POSIX time p; leap marks a reading taken during an
// inserted leap second (p is then the second before it).
func Instant(w io.Writer, p int64, leap bool, z posixtz.Zone) error {
	_, err := fmt.Fprintf(w, `{"utc":%s,"local":%s,"offset":%d,"abbr":%s,"isdst":%t}`+"\n",
		strconv.Quote(civil.FormatLeap(p, leap)+"Z"), strconv.Quote(civil.FormatLeap(p+z.Offset, leap)), z.Offset, strconv.Quote(z.Abbr), z.IsDST)
	return err
}

// Transition writes one change of local time type taking effect at the
// instant whose UTC reading is p (see Instant for leap).
func Transition(w io.Writer, p int64, leap bool, z posixtz.Zone) error {
	_, err := fmt.Fprintf(w, `{"at":%s,"offset":%d,"abbr":%s,"isdst":%t}`+"\n",
		strconv.Quote(civil.FormatLeap(p, leap)+"Z"), z.Offset, strconv.Quote(z.Abbr), z.IsDST)
	return err
}
EOF

cat > cmd/shiftclock/at.go <<'EOF'
package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"strconv"

	"shiftclock/internal/civil"
	"shiftclock/internal/report"
	"shiftclock/internal/tzif"
)

func runAt(args []string) error {
	fs := flag.NewFlagSet("at", flag.ContinueOnError)
	zone := fs.String("zone", "", "TZif file or zone name")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if fs.NArg() == 0 {
		return fmt.Errorf("at: no instants given")
	}
	f, err := openZone(*zone)
	if err != nil {
		return err
	}
	instants := make([]int64, 0, fs.NArg())
	for _, s := range fs.Args() {
		t, err := parseInstant(f, s)
		if err != nil {
			return err
		}
		instants = append(instants, t)
	}
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for _, t := range instants {
		p, leap := f.UTC(t)
		if err := report.Instant(w, p, leap, f.Lookup(t)); err != nil {
			return err
		}
	}
	return nil
}

// parseInstant reads Unix seconds as an instant of f's time scale, and an
// RFC 3339 UTC reading through f's leap-second records.
func parseInstant(f *tzif.File, s string) (int64, error) {
	if n, err := strconv.ParseInt(s, 10, 64); err == nil {
		return n, nil
	}
	p, sec60, err := civil.ParseUTC(s)
	if err != nil {
		return 0, err
	}
	t := f.Instant(p)
	if sec60 {
		t++
		if _, leap := f.UTC(t); !leap {
			return 0, fmt.Errorf("instant %q: not a leap second in this zone file", s)
		}
	}
	return t, nil
}
EOF

cat > cmd/shiftclock/transitions.go <<'EOF'
package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"

	"shiftclock/internal/civil"
	"shiftclock/internal/report"
)

func runTransitions(args []string) error {
	fs := flag.NewFlagSet("transitions", flag.ContinueOnError)
	zone := fs.String("zone", "", "TZif file or zone name")
	fromYear := fs.Int64("from", 0, "first UTC year (inclusive)")
	toYear := fs.Int64("to", 0, "last UTC year (inclusive)")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *fromYear == 0 || *toYear == 0 || *toYear < *fromYear {
		return fmt.Errorf("transitions: need --from YEAR --to YEAR with from <= to")
	}
	f, err := openZone(*zone)
	if err != nil {
		return err
	}
	from := f.Instant(civil.DaysFromCivil(*fromYear, 1, 1) * civil.SecondsPerDay)
	to := f.Instant(civil.DaysFromCivil(*toYear+1, 1, 1) * civil.SecondsPerDay)
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for _, tr := range f.Transitions(from, to) {
		p, leap := f.UTC(tr.At)
		if err := report.Transition(w, p, leap, tr.Zone); err != nil {
			return err
		}
	}
	return nil
}
EOF

test -z "$(gofmt -l internal cmd)"
go vet ./...
go build ./cmd/shiftclock
rm -f shiftclock
