package resolve

import (
	"github.com/brightloom/pinwheel/internal/registry"
	"github.com/brightloom/pinwheel/internal/semrange"
)

// pinned reports whether one of the constraints pins rel exactly, which is
// the only way a yanked release can still be locked.
func pinned(rel *registry.Release, cons []Constraint) bool {
	for _, c := range cons {
		if exactPin(c.Range) && c.Range.Test(rel.Parsed) {
			return true
		}
	}
	return false
}

func exactPin(r semrange.Range) bool {
	if len(r.Sets) != 1 || len(r.Sets[0]) != 1 {
		return false
	}
	c := r.Sets[0][0]
	return !c.Any && c.Op == semrange.OpEQ
}
