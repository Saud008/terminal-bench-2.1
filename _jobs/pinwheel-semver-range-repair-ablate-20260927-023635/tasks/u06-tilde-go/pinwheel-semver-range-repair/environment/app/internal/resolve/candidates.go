package resolve

import (
	"sort"

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
	sort.SliceStable(eligible, func(i, j int) bool {
		if c := semver.Compare(eligible[i].Parsed, eligible[j].Parsed); c != 0 {
			return c < 0
		}
		return eligible[i].Published.Before(eligible[j].Published)
	})
	if lowest {
		return eligible[0], nil
	}
	return eligible[len(eligible)-1], nil
}

func satisfiesAll(rel *registry.Release, cons []Constraint) bool {
	for _, c := range cons {
		if !c.Range.Test(rel.Parsed) {
			return false
		}
	}
	return true
}