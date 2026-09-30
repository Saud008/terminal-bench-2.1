package semrange

import "github.com/brightloom/pinwheel/internal/semver"

// xrange expands a plain or operator-prefixed partial: "1.2.3", "=1.2.3",
// "1.x", ">1.2", "<=2", "*".
func xrange(op string, p partial) []Comparator {
	if p.fields == 3 {
		return []Comparator{{Op: opFor(op), Version: p.version()}}
	}
	if p.fields == 0 {
		if op == "<" || op == ">" {
			return []Comparator{matchNone}
		}
		return []Comparator{matchAll}
	}
	lo := semver.New(p.major, p.minor, 0)
	switch op {
	case ">":
		return []Comparator{{Op: OpGT, Version: lo}}
	case ">=":
		return []Comparator{{Op: OpGTE, Version: lo}}
	case "<":
		return []Comparator{{Op: OpLT, Version: lo.Floor()}}
	case "<=":
		return []Comparator{{Op: OpLTE, Version: lo}}
	}
	return between(lo, p.next())
}

func opFor(op string) Op {
	switch op {
	case "<":
		return OpLT
	case "<=":
		return OpLTE
	case ">":
		return OpGT
	case ">=":
		return OpGTE
	}
	return OpEQ
}
