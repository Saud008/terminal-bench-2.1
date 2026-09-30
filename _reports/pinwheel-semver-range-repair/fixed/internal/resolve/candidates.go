package resolve

import (
	"github.com/brightloom/pinwheel/internal/registry"
	"github.com/brightloom/pinwheel/internal/semver"
)

// choose picks the release of pkg to lock under the given constraints.
func choose(pkg *registry.Package, cons []Constraint, lowest bool) (*registry.Release, error) {
	var eligible []*registry.Release
	for i := range pkg.Releases {
		rel := &pkg.Releases[i]
		if !satisfiesAll(rel, cons) {
			continue
		}
		if rel.Yanked && !pinned(rel, cons) {
			continue
		}
		eligible = append(eligible, rel)
	}
	if len(eligible) == 0 {
		return nil, &UnsatisfiableError{Package: pkg.Name, Constraints: cons}
	}
	best := eligible[0]
	for _, rel := range eligible[1:] {
		if preferred(rel, best, lowest) {
			best = rel
		}
	}
	return best, nil
}

func satisfiesAll(rel *registry.Release, cons []Constraint) bool {
	for _, c := range cons {
		if !c.Range.Test(rel.Parsed) {
			return false
		}
	}
	return true
}

// preferred reports whether a should be locked instead of b.
func preferred(a, b *registry.Release, lowest bool) bool {
	if c := semver.Compare(a.Parsed, b.Parsed); c != 0 {
		if lowest {
			return c < 0
		}
		return c > 0
	}
	if !a.Published.Equal(b.Published) {
		return a.Published.After(b.Published)
	}
	return a.Index > b.Index
}
