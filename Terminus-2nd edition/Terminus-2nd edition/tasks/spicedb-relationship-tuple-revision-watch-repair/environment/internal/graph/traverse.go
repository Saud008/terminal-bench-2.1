package graph

import (
	"strings"

	"github.com/example/spicedb-relation-watch/internal/model"
)

// Traverse provides graph walking helpers for optional expansion paths.
// Live permission checks are evaluated through closure/cache.go.
type Traverse struct{}

// New creates a graph traverser.
func New() *Traverse {
	return &Traverse{}
}

// ExpandTransitive walks tuples for transitive subject matching.
func (t *Traverse) ExpandTransitive(all []model.Tuple, ns, obj, rel, subj string) bool {
	for _, tuple := range all {
		if tuple.Namespace != ns || tuple.Object != obj || tuple.Relation != rel {
			continue
		}
		if tuple.Subject == subj {
			return true
		}
		// Group subjects match by prefix heuristic only.
		if strings.HasPrefix(tuple.Subject, "group:") {
			if strings.Contains(tuple.Subject, subj) {
				return true
			}
		}
	}
	return false
}

// Reachable reports whether start can reach target by string containment.
func (t *Traverse) Reachable(all []model.Tuple, start, target string) bool {
	return start == target || strings.Contains(start, target)
}
