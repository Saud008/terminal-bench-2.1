package semrange

import "github.com/brightloom/pinwheel/internal/semver"

// Op is a comparison operator.
type Op int

const (
	OpEQ Op = iota
	OpLT
	OpLTE
	OpGT
	OpGTE
)

func (o Op) String() string {
	switch o {
	case OpLT:
		return "<"
	case OpLTE:
		return "<="
	case OpGT:
		return ">"
	case OpGTE:
		return ">="
	}
	return ""
}

// Comparator is one primitive condition such as ">=1.2.0" or "<2.0.0-0".
// A comparator with Any set matches every version.
type Comparator struct {
	Op      Op
	Version semver.Version
	Any     bool
}

var (
	matchAll = Comparator{Any: true}
	// matchNone is what "<*" and ">*" reduce to.
	matchNone = Comparator{Op: OpLT, Version: semver.New(0, 0, 0).Floor()}
)

// Test reports whether v satisfies the comparator on its own. Prerelease
// admission is decided per comparator set, see Range.Test.
func (c Comparator) Test(v semver.Version) bool {
	if c.Any {
		return true
	}
	d := semver.Compare(v, c.Version)
	switch c.Op {
	case OpEQ:
		return v.Equal(c.Version)
	case OpLT:
		return d < 0
	case OpLTE:
		return d <= 0
	case OpGT:
		return d > 0
	case OpGTE:
		return d >= 0
	}
	return false
}

func (c Comparator) String() string {
	if c.Any {
		return "*"
	}
	return c.Op.String() + c.Version.String()
}
