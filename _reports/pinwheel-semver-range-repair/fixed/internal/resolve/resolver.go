// Package resolve computes the flat set of releases a project locks.
package resolve

import (
	"fmt"

	"github.com/brightloom/pinwheel/internal/manifest"
	"github.com/brightloom/pinwheel/internal/registry"
)

const maxRounds = 100

// Result is a settled resolution.
type Result struct {
	// Selected maps every required package to its locked release.
	Selected map[string]*registry.Release
	// Constraints holds, per package, the ranges its dependents wrote for it.
	Constraints map[string][]Constraint
}

// Resolve runs resolution rounds until the selection stops changing.
func Resolve(m *manifest.Manifest, reg *registry.Registry) (*Result, error) {
	sel := map[string]*registry.Release{}
	for round := 0; round < maxRounds; round++ {
		cons, err := gather(m, sel)
		if err != nil {
			return nil, err
		}
		next := make(map[string]*registry.Release, len(cons))
		for _, name := range sortedKeys(cons) {
			pkg, ok := reg.Package(name)
			if !ok {
				return nil, &UnknownPackageError{Package: name, RequiredBy: dependents(cons[name])}
			}
			rel, err := choose(pkg, effective(m, name, cons[name]), m.PreferLowest())
			if err != nil {
				return nil, err
			}
			next[name] = rel
		}
		if sameSelection(sel, next) {
			return &Result{Selected: next, Constraints: cons}, nil
		}
		sel = next
	}
	return nil, fmt.Errorf("resolution did not settle after %d rounds", maxRounds)
}

func sameSelection(a, b map[string]*registry.Release) bool {
	if len(a) != len(b) {
		return false
	}
	for name, rel := range a {
		if b[name] != rel {
			return false
		}
	}
	return true
}
