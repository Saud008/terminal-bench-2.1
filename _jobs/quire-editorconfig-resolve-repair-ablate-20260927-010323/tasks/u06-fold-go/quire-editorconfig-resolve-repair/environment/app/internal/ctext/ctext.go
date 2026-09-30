// Package ctext holds the byte-level character rules quire shares with the
// C core: ASCII-only case folding, C isspace/isalnum and strtol-style numbers.
package ctext

import "math"

// IsSpace reports whether c is one of the six C whitespace characters.
func IsSpace(c byte) bool {
	return c == ' ' || c == '\t' || c == '\n' || c == '\v' || c == '\f' || c == '\r'
}

// IsAlnum reports whether c is an ASCII letter or digit.
func IsAlnum(c byte) bool {
	return c >= '0' && c <= '9' || c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z'
}

// Lower lowercases ASCII letters and leaves every other byte alone.
func Lower(s string) string {
	b := []byte(s)
	for i, c := range b {
		if c >= 'A' && c <= 'Z' {
			b[i] = c + ('a' - 'A')
		}
	}
	return string(b)
}

// EqualFold compares two strings ignoring ASCII case only.
func EqualFold(a, b string) bool {
	return len(a) == len(b) && Lower(a) == Lower(b)
}

// TrimRight removes trailing whitespace.
func TrimRight(s string) string {
	for len(s) > 0 && IsSpace(s[len(s)-1]) {
		s = s[:len(s)-1]
	}
	return s
}

// TrimLeft removes leading whitespace.
func TrimLeft(s string) string {
	for len(s) > 0 && IsSpace(s[0]) {
		s = s[1:]
	}
	return s
}

// Atoi converts the leading decimal number of s the way strtol does:
// optional leading whitespace and sign, digits up to the first non-digit,
// 0 when there are no digits. Out-of-range values saturate and are then
// narrowed to a C int.
func Atoi(s string) int {
	i := 0
	for i < len(s) && IsSpace(s[i]) {
		i++
	}
	neg := false
	if i < len(s) && (s[i] == '+' || s[i] == '-') {
		neg = s[i] == '-'
		i++
	}
	var n uint64
	overflow := false
	for ; i < len(s) && s[i] >= '0' && s[i] <= '9'; i++ {
		if n > (math.MaxInt64-9)/10 {
			overflow = true
			continue
		}
		n = n*10 + uint64(s[i]-'0')
	}
	var v int64
	switch {
	case overflow && neg:
		v = math.MinInt64
	case overflow:
		v = math.MaxInt64
	case neg:
		v = -int64(n)
	default:
		v = int64(n)
	}
	return int(int32(v))
}
