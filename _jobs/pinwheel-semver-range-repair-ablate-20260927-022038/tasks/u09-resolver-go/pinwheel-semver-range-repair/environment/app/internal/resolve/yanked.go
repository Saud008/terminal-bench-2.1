package resolve

import (
	"strings"

	"github.com/brightloom/pinwheel/internal/registry"
)

// pinned reports whether one of the constraints pins rel exactly, which is
// the only way a yanked release can still be locked.
func pinned(rel *registry.Release, cons []Constraint) bool {
	for _, c := range cons {
		if strings.HasPrefix(strings.TrimSpace(c.Raw), "=") && c.Range.Test(rel.Parsed) {
			return true
		}
	}
	return false
}
