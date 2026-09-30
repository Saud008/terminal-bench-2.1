package posixtz

import (
	"fmt"
	"strconv"
	"strings"
)

// defaultRuleTime is used when a rule omits its "/time" part.
const defaultRuleTime = 2 * 3600

type parser struct {
	s   string
	pos int
}

// Parse parses a TZ string such as "EST5EDT,M3.2.0,M11.1.0".
func Parse(s string) (*TZ, error) {
	p := &parser{s: s}
	tz := &TZ{Raw: s}
	var err error
	if tz.Std, err = p.name(); err != nil {
		return nil, err
	}
	off, err := p.offset()
	if err != nil {
		return nil, err
	}
	tz.StdOffset = -off // POSIX offsets are positive west of Greenwich
	if p.done() {
		return tz, nil
	}
	tz.HasDST = true
	if tz.Dst, err = p.name(); err != nil {
		return nil, err
	}
	tz.DstOffset = tz.StdOffset + 3600
	if !p.done() && p.peek() != ',' {
		if off, err = p.offset(); err != nil {
			return nil, err
		}
		tz.DstOffset = -off
	}
	if p.done() {
		// No rules given: fall back to the current US rules, as tzcode does.
		tz.Start = Rule{Kind: MonthWeekDay, Month: 3, Week: 2, Weekday: 0, Time: defaultRuleTime}
		tz.End = Rule{Kind: MonthWeekDay, Month: 11, Week: 1, Weekday: 0, Time: defaultRuleTime}
		return tz, nil
	}
	if err = p.expect(','); err != nil {
		return nil, err
	}
	if tz.Start, err = p.rule(); err != nil {
		return nil, err
	}
	if err = p.expect(','); err != nil {
		return nil, err
	}
	if tz.End, err = p.rule(); err != nil {
		return nil, err
	}
	if !p.done() {
		return nil, p.errorf("trailing characters")
	}
	return tz, nil
}

func (p *parser) done() bool { return p.pos >= len(p.s) }

func (p *parser) peek() byte { return p.s[p.pos] }

func (p *parser) errorf(format string, args ...any) error {
	return fmt.Errorf("posixtz: %q at offset %d: %s", p.s, p.pos, fmt.Sprintf(format, args...))
}

func (p *parser) expect(c byte) error {
	if p.done() || p.peek() != c {
		return p.errorf("expected %q", c)
	}
	p.pos++
	return nil
}

// name reads an abbreviation: either <...> quoted or a run of letters.
func (p *parser) name() (string, error) {
	if !p.done() && p.peek() == '<' {
		end := strings.IndexByte(p.s[p.pos:], '>')
		if end < 0 {
			return "", p.errorf("unterminated quoted name")
		}
		n := p.s[p.pos+1 : p.pos+end]
		p.pos += end + 1
		if len(n) < 3 {
			return "", p.errorf("name %q too short", n)
		}
		return n, nil
	}
	start := p.pos
	for !p.done() && isAlpha(p.peek()) {
		p.pos++
	}
	if p.pos-start < 3 {
		return "", p.errorf("name too short")
	}
	return p.s[start:p.pos], nil
}

// token returns the text up to the next ',' or the end of the string.
func (p *parser) token(stop string) string {
	start := p.pos
	for !p.done() && !strings.ContainsRune(stop, rune(p.peek())) {
		p.pos++
	}
	return p.s[start:p.pos]
}

// offset reads a UTC offset such as "5", "-10", "+3:30" or "-12:45".
func (p *parser) offset() (int64, error) {
	start := p.pos
	if !p.done() && (p.peek() == '+' || p.peek() == '-') {
		p.pos++
	}
	for !p.done() && (isDigit(p.peek()) || p.peek() == ':') {
		p.pos++
	}
	secs, err := parseHMS(p.s[start:p.pos], 24, true)
	if err != nil {
		return 0, p.errorf("offset: %v", err)
	}
	return secs, nil
}

func (p *parser) rule() (Rule, error) {
	var r Rule
	spec := p.token(",/")
	switch {
	case strings.HasPrefix(spec, "M"):
		parts := strings.Split(spec[1:], ".")
		if len(parts) != 3 {
			return r, p.errorf("bad month rule %q", spec)
		}
		var vals [3]int
		for i, s := range parts {
			n, err := strconv.Atoi(s)
			if err != nil {
				return r, p.errorf("bad month rule %q", spec)
			}
			vals[i] = n
		}
		if vals[0] < 1 || vals[0] > 12 || vals[1] < 1 || vals[1] > 5 || vals[2] < 0 || vals[2] > 6 {
			return r, p.errorf("month rule %q out of range", spec)
		}
		r = Rule{Kind: MonthWeekDay, Month: vals[0], Week: vals[1], Weekday: vals[2]}
	case strings.HasPrefix(spec, "J"):
		n, err := strconv.Atoi(spec[1:])
		if err != nil || n < 1 || n > 365 {
			return r, p.errorf("bad Julian day %q", spec)
		}
		r = Rule{Kind: JulianNoLeap, Day: n}
	default:
		n, err := strconv.Atoi(spec)
		if err != nil || n < 0 || n > 365 {
			return r, p.errorf("bad day %q", spec)
		}
		r = Rule{Kind: ZeroBased, Day: n}
	}
	r.Time = defaultRuleTime
	if !p.done() && p.peek() == '/' {
		p.pos++
		t, err := parseRuleTime(p.token(","))
		if err != nil {
			return r, p.errorf("rule time: %v", err)
		}
		r.Time = t
	}
	return r, nil
}

func isAlpha(c byte) bool { return c >= 'A' && c <= 'Z' || c >= 'a' && c <= 'z' }

func isDigit(c byte) bool { return c >= '0' && c <= '9' }
