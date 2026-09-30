package resolve

import (
	"fmt"
	"sort"

	"github.com/brightloom/pinwheel/internal/manifest"
	"github.com/brightloom/pinwheel/internal/registry"
	"github.com/brightloom/pinwheel/internal/semrange"
)

const (
	// RootName stands for the project itself as a dependent.
	RootName = "<root>"
	// OverrideName is the source recorded for a constraint from "overrides".
	OverrideName = "<overrides>"
)

// Constraint is one range some dependent placed on a package.
type Constraint struct {
	From  string
	Raw   string
	Range semrange.Range
}

// gather walks from the project's dependencies through the dependencies of
// the selected releases and returns the constraints on every package reached.
// Packages reached but not selected yet contribute no constraints of their own.
func gather(m *manifest.Manifest, sel map[string]*registry.Release) (map[string][]Constraint, error) {
	cons := map[string][]Constraint{}
	var queue []string
	add := func(from, name, raw string) error {
		r, err := semrange.Parse(raw)
		if err != nil {
			return fmt.Errorf("%s depends on %s: %w", from, name, err)
		}
		if _, seen := cons[name]; !seen {
			queue = append(queue, name)
		}
		cons[name] = append(cons[name], Constraint{From: from, Raw: raw, Range: r})
		return nil
	}
	for _, name := range sortedKeys(m.Dependencies) {
		if err := add(RootName, name, m.Dependencies[name]); err != nil {
			return nil, err
		}
	}
	for len(queue) > 0 {
		name := queue[0]
		queue = queue[1:]
		rel, ok := sel[name]
		if !ok {
			continue
		}
		for _, dep := range sortedKeys(rel.Dependencies) {
			if err := add(name, dep, rel.Dependencies[dep]); err != nil {
				return nil, err
			}
		}
	}
	return cons, nil
}

// effective returns the constraints a release of name has to meet.
func effective(m *manifest.Manifest, name string, cons []Constraint) []Constraint {
	raw, ok := m.Overrides[name]
	if !ok {
		return cons
	}
	out := append([]Constraint(nil), cons...)
	return append(out, Constraint{From: OverrideName, Raw: raw, Range: semrange.MustParse(raw)})
}

func sortedKeys[V any](m map[string]V) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}
