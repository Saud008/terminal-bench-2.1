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
		changed := false
		for _, name := range sortedKeys(cons) {
			pkg, ok := reg.Package(name)
			if !ok {
				return nil, &UnknownPackageError{Package: name, RequiredBy: dependents(cons[name])}
			}
			rel, err := choose(pkg, effective(m, name, cons[name]), m.PreferLowest())
			if err != nil {
				return nil, err
			}
			if sel[name] != rel {
				sel[name] = rel
				changed = true
			}
		}
		if !changed {
			return &Result{Selected: sel, Constraints: cons}, nil
		}
	}
	return nil, fmt.Errorf("resolution did not settle after %d rounds", maxRounds)
}
